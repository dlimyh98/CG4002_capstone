#define EXCLUDE_EXOTIC_PROTOCOLS
#define EXCLUDE_UNIVERSAL_PROTOCOLS
#define DECODE_NEC
#define RECORD_GAP_MICROS 4550
#include <IRremote.hpp>
#include <TM1637Display.h>

/********************************************* IMPORTANT *********************************************/
/*
    tone() and IRremote.hpp uses the SAME timer for their functionalities.
    Therefore, if you do not change their timer definitions, they will conflict and IRremote will be unable to work (e.g. cant print IrReceiver.decodedIRdata will be inconsistent)
    - To solve this, goto .../Arduino/libraries/IRremote/src/private/IRTimer.hpp
    - Assuming using ATmega328p board, change #define IR_USE_TIMER2 to #define IR_USE_TIMER1 
******************************************************************************************************/

#define SEG_IO_PIN 2        // D2, I/O for 7SEG
#define SEG_CLK_PIN 3       // D3 PWM,functionality for 7SEG's CLK
#define IR_RECEIVE_PIN 4    // D4, I/O
#define RESET_SWITCH 5      // D5, reset switch
#define PIE_PIN A0          // A0 functionality for Piezo's IN

#define FLASH_PLAYER_ONE_BLUE_DOTS
//#define FLASH_PLAYER_TWO_NO_BLUE_DOTS

int current_reset_switch_state;
int last_reset_switch_state;
unsigned long last_debounce_time_reset_switch;
unsigned long debounce_delay_reset_switch;

const uint8_t FULL_HEALTH[] = {
  0x0,                                            // OFF
  SEG_B | SEG_C,                                  // 1
  SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F,  // 0
  SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F   // 0
};

const uint8_t NINETY_HEALTH[] = {
  0x0, 0x0,
  SEG_D | SEG_C | SEG_B | SEG_A | SEG_F | SEG_G,  // 9
  SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F   // 0
};

const uint8_t EIGHTY_HEALTH[] = {
  0x0, 0x0,
  SEG_D | SEG_C | SEG_B | SEG_A | SEG_F | SEG_G | SEG_E,  // 8
  SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F           // 0
};

const uint8_t SEVENTY_HEALTH[] = {
  0x0, 0x0,
  SEG_C | SEG_B | SEG_A,                          // 7
  SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F   // 0
};

const uint8_t SIXTY_HEALTH[] = {
  0x0, 0x0,
  SEG_D | SEG_C | SEG_A | SEG_F | SEG_G | SEG_E,  // 6
  SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F   // 0
};

const uint8_t FIFTY_HEALTH[] = {
  0x0, 0x0,
  SEG_D | SEG_C | SEG_A | SEG_F | SEG_G,          // 5
  SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F   // 0
};

const uint8_t FOURTY_HEALTH[] = {
  0x0, 0x0,
  SEG_C | SEG_B | SEG_F | SEG_G,                  // 4
  SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F   // 0
};

const uint8_t THIRTY_HEALTH[] = {
  0x0, 0x0,
  SEG_D | SEG_C | SEG_B | SEG_A | SEG_G,          // 3
  SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F   // 0
};

const uint8_t TWENTY_HEALTH[] = {
  0x0, 0x0,
  SEG_D | SEG_B | SEG_A | SEG_G | SEG_E,  // 8
  SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F   // 0
};

const uint8_t TEN_HEALTH[] = {
  0x0, 0x0,
  SEG_C | SEG_B,                                  // 1
  SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F   // 0
};

const uint8_t GAME_OVER[] = {
  SEG_B | SEG_C | SEG_D | SEG_E | SEG_G,           // d
  SEG_G | SEG_A | SEG_F | SEG_E | SEG_D,           // E
  SEG_E | SEG_F | SEG_A | SEG_B | SEG_C | SEG_G,   // A 
  SEG_B | SEG_C | SEG_D | SEG_E | SEG_G,           // d

};

int num_of_times_shot;

// Create a display object of type TM1637Display
TM1637Display display = TM1637Display(SEG_CLK_PIN, SEG_IO_PIN);

void seven_seg_init();
void IR_receive_init();
void reset_switch_init();

void handle_being_shot();
void handle_reset_swich();

void setup() {
  Serial.begin(9600);
  reset_switch_init();
  seven_seg_init();
  delay(1000);
  IR_receive_init();
}

void loop() {
  if (IrReceiver.decode()) {
    IRData results = IrReceiver.decodedIRData;

    #ifdef FLASH_PLAYER_ONE_BLUE_DOTS
      if (results.address == 0x100 && results.command == 0x35) {
        handle_being_shot();
      }
    #endif

    #ifdef FLASH_PLAYER_TWO_NO_BLUE_DOTS
    if (results.address == 0x101 && results.command == 0x36) {
      handle_being_shot();
    }
    #endif

    IrReceiver.resume(); // Important, enables to receive the next IR signal
  }

  // Common functions
  //handle_internal_comms();
  update_sevenseg();
  handle_reset_switch();
}

void handle_internal_comms() {
  // Receive packet and decode
  int received_health = Serial.read();
  num_of_times_shot = (100 - received_health) / 10;
}

void handle_being_shot() {
  // Shot counter increases (stops at 10 shots, since that is limit until reset)
  num_of_times_shot = (num_of_times_shot == 10) ? num_of_times_shot : num_of_times_shot + 1;

  // Play corresponding audio-tune
  if (num_of_times_shot != 10) {
    // Beep once
    tone(PIE_PIN, 500, 250);
  } else {
    // Beep a scale
    tone(PIE_PIN,261,150); delay(250);
    tone(PIE_PIN,294,150); delay(250);
    tone(PIE_PIN,330,150); delay(250);
    tone(PIE_PIN,261,150); delay(250);
    tone(PIE_PIN,294,150); delay(250);
    noTone(PIE_PIN);
  }
}

void update_sevenseg() {
  // Update SEVENSEG
  switch(num_of_times_shot) {

    case 0:
      display.setSegments(FULL_HEALTH, 4, 0);
      break;

    case 1 : 
      display.setSegments(NINETY_HEALTH, 4, 0);
      break;

    case 2 : 
      display.setSegments(EIGHTY_HEALTH, 4, 0);
      break;

    case 3 : 
      display.setSegments(SEVENTY_HEALTH, 4, 0);
      break;

    case 4 : 
      display.setSegments(SIXTY_HEALTH, 4, 0);
      break;

    case 5 : 
      display.setSegments(FIFTY_HEALTH, 4, 0);
      break;

    case 6 : 
      display.setSegments(FOURTY_HEALTH, 4, 0);
      break;

    case 7 : 
      display.setSegments(THIRTY_HEALTH, 4, 0);
      break;

    case 8 : 
      display.setSegments(TWENTY_HEALTH, 4, 0);
      break;

    case 9 : 
      display.setSegments(TEN_HEALTH, 4, 0);
      break;

    case 10 : 
      display.setSegments(GAME_OVER, 4, 0);
      break;
  }
}

void handle_reset_switch() {
  int reading = digitalRead(RESET_SWITCH);

  if (reading != last_reset_switch_state) {
    // Change detected, reset debounce timer
    last_debounce_time_reset_switch = millis();
  }

  if ((millis() - last_debounce_time_reset_switch) > debounce_delay_reset_switch) {
      // Whatever reading is, it's been there longer than debounce delay. Take the reading as is
      if (reading != current_reset_switch_state) {
        // assert that reading is NOT due to debouncing
        num_of_times_shot = 0;
        IR_receive_init();
        current_reset_switch_state = reading;
      }
  }

  last_reset_switch_state = reading;
}

void seven_seg_init(){
  display.setBrightness(0x0f);
  display.setSegments(FULL_HEALTH, 4, 0);
}

void IR_receive_init() {
  // Serial.begin(9600);
  IrReceiver.begin(IR_RECEIVE_PIN);
  num_of_times_shot = 0;
}

void reset_switch_init() {
  // RESET_SWITCH is connected to Vdd initially
  // When reset switch is pressed, connected to GND
  pinMode(RESET_SWITCH, INPUT_PULLUP);

  // Debouncing the reset trigger
  current_reset_switch_state = HIGH; // Pin is in active high configuration
  last_reset_switch_state = HIGH;    // Pin is in active high configuration
  last_debounce_time_reset_switch = 0;
  debounce_delay_reset_switch = 100;
}