
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

#define ACK 1
#define VEST_BEETLE_DATA 3 // TO CHANGE: Type; which beetle data is coming from.
#define MAX_SEQ_NO 10
#define INTERVAL 40 // Make sure this syncs up with the timeout/interval on Python

int current_reset_switch_state;
int last_reset_switch_state;
unsigned long last_debounce_time_reset_switch;
unsigned long debounce_delay_reset_switch;
uint16_t updatedHealth = 100;
uint16_t updatedShotStatus = 0;


// ACK packet to acknowledge handshake initiation; to be sent to python
struct Ackpacket {
  uint8_t type; //b
  uint16_t padding_1; //h
  uint16_t padding_2; //h
  uint16_t padding_3; //h
  uint16_t padding_4; //h
  uint16_t padding_5; //h
  uint16_t padding_6; //h
  uint16_t padding_7; //h
  uint8_t padding_8; //b
  uint32_t crcsum; //i
};
// Data packet to be sent to python
struct Datapacket {
  uint8_t type;
  uint16_t shotStatus; // 1 for shot, 0 for miss
  uint16_t health; // Health represented by seven-seg
  uint16_t padding_1;
  uint16_t padding_2;
  uint16_t padding_3;
  uint16_t padding_4;
  uint16_t sequence_number;
  uint8_t padding_5;
  uint32_t crcsum;
};

uint8_t seq_no;
uint8_t prev_seq_no;
unsigned long ack_timer;
char currentState;
bool sentHandshakeAck;
bool ackReceived;
char msg;
unsigned long lastPacketSentTime = 0;
unsigned long ackTimeout = 2000;

uint8_t updatedBulletCount = 0;

// Packets sent tracker; for if resend required.
Datapacket sentPackets[MAX_SEQ_NO + 1];

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
  // put your setup code here, to run once:
  Serial.begin(115200); 
  resetFlags();
  reset_switch_init();
  seven_seg_init();
  delay(1000);
}

void loop() {
  // put your main code here, to run repeatedly:
   if (Serial.available()) {
    // if there are updates from external comms.
    if (Serial.peek() == 'g') 
      currentState = Serial.read();
    // initiating handshake signal
    if (Serial.peek() == 'h') 
      currentState = Serial.read();
  }
  switch(currentState) {
    case 's':
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
      break;
//    case 'a':
//      waitForAck();
//      // Acknowledgment received, change the state to 's' to send the next packet
//      if (ackReceived) {
//        // If no updates; updates signalled if 'g' received.
//        if (currentState != 'g'){
//          setStateToSend();
//          ackReceived = false;
//        }
//      } 
//      break;
    case 'g':
      if (Serial.available() >= sizeof(uint8_t)) {
        uint8_t receivedByte = Serial.read();
        updatedHealth = receivedByte;
        update_sevenseg();
        setStateToSend();
      }
      break;
    case 'h':
      resetFlags();
      sendHandshakeAck();
      waitForHandshakeAck();
      break;
    case 'i':
      IR_receive_init();
      delay(1000);
      setStateToSend();
      break;
    default:
      resetFlags();
      break;
  }
  handle_reset_switch();
}
// ================ Data Transmission and Handling =================
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
    updatedShotStatus = 1;
//    updatedHealth = (10 - num_of_times_shot) * 10;
//    setStateToSend();
  } else {
    // Beep a scale
    tone(PIE_PIN,261,150); delay(250);
    tone(PIE_PIN,294,150); delay(250);
    tone(PIE_PIN,330,150); delay(250);
    tone(PIE_PIN,261,150); delay(250);
    tone(PIE_PIN,294,150); delay(250);
    noTone(PIE_PIN);
    updatedShotStatus = 1;
//    setStateToSend();
  }
  sendBeetleData(VEST_BEETLE_DATA);
  updatedShotStatus = 0;
  setStateToSend();
//  ackReceived = false;
//  lastPacketSentTime = millis();
//  setStateToAck();
}

void sendBeetleData(uint8_t type) {
  Datapacket packet;
  packet.type = type;
  packet.sequence_number = seq_no;
  prev_seq_no = seq_no;
  if(seq_no < MAX_SEQ_NO){
    seq_no++; // Increment the sequence number for the next packet
  } else {
    seq_no = 0;
  }
  packet.shotStatus = updatedShotStatus;
  packet.health = updatedHealth;
  packet.crcsum = calculateDataCrc32(&packet);
  sentPackets[packet.sequence_number] = packet;
  Serial.write((uint8_t *)&packet, sizeof(packet));
  delay(INTERVAL);
}
// =======================================================
// ================ Hardware Code =================
void update_sevenseg() {
  // Update SEVENSEG
  switch(updatedHealth) {

    case 100:
      display.setSegments(FULL_HEALTH, 4, 0);
      break;

    case 90: 
      display.setSegments(NINETY_HEALTH, 4, 0);
      break;

    case 80: 
      display.setSegments(EIGHTY_HEALTH, 4, 0);
      break;

    case 70: 
      display.setSegments(SEVENTY_HEALTH, 4, 0);
      break;

    case 60: 
      display.setSegments(SIXTY_HEALTH, 4, 0);
      break;

    case 50: 
      display.setSegments(FIFTY_HEALTH, 4, 0);
      break;

    case 40: 
      display.setSegments(FOURTY_HEALTH, 4, 0);
      break;

    case 30: 
      display.setSegments(THIRTY_HEALTH, 4, 0);
      break;

    case 20: 
      display.setSegments(TWENTY_HEALTH, 4, 0);
      break;

    case 10: 
      display.setSegments(TEN_HEALTH, 4, 0);
      break;

    case 0: 
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
        updatedHealth = 100;
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

// =======================================================

//================ Handshake =================

void sendHandshakeAck() {
  if (sentHandshakeAck) return;
  Ackpacket packet;
  packet.type = ACK;
  packet.padding_1 = 0;
  packet.padding_2 = 0;
  packet.padding_3 = 0;
  packet.padding_4 = 0;
  packet.padding_5 = 0;
  packet.padding_6 = 0;
  packet.padding_7 = 0;
  packet.padding_8 = 0;
  packet.crcsum = calculateAckCrc32(&packet);
  Serial.write((uint8_t *)&packet, sizeof(packet));
  sentHandshakeAck = true;
}

void waitForHandshakeAck(){
  char ack_msg;

  while (!Serial.available());
  ack_msg = Serial.read();

  if (ack_msg != 'v') {
    resetFlags();
    return;
  }

  setStateToIrReceive();

}

void resetFlags() {
  sentHandshakeAck = false;
  ackReceived = false;
  seq_no = 0;
  updatedBulletCount = 0;
}

//=======================================================

//================ State Machine =================
void setStateToSend() {
  currentState = 's';
}

void setStateToAck() {
  currentState = 'a';
}

void setStateToGamestate(){
  currentState = 'g';
}

void setStateToIrReceive(){
  currentState = 'i';
}

void setStateToHandshake() {
  currentState = 'h';
  sentHandshakeAck = false;
}
//===========================================================

//================ Stop and Wait Protocol =================
void waitForAck() {
    uint8_t ack_seq_no = Serial.read();
    if (ack_seq_no == prev_seq_no) {
      ackReceived = true;
      return;
    } else if (millis() - lastPacketSentTime >= ackTimeout) {
//      Serial.print("Entered");
      // Timeout: No acknowledgment received, retransmit the packet
      sendPacket(sentPackets[prev_seq_no]); // Change the state to 's' to retransmit the packet
      lastPacketSentTime = millis();
    }
    return;
}

void sendPacket(Datapacket packet) {
  Serial.write((uint8_t *)&packet, sizeof(packet));
}
//===========================================================

//========================Calculate CRC======================

uint32_t calculateDataCrc32(Datapacket *pkt) {
  return custom_crc32(&pkt->type, 
    sizeof(pkt->type) +
    sizeof(pkt->shotStatus) +
    sizeof(pkt->health) +
    sizeof(pkt->padding_1) +
    sizeof(pkt->padding_2) +
    sizeof(pkt->padding_3) +
    sizeof(pkt->padding_4) +
    sizeof(pkt->sequence_number) +
    sizeof(pkt->padding_5)
  );
}

uint32_t calculateAckCrc32(Ackpacket *pkt) {
  return custom_crc32(&pkt->type, 
    sizeof(pkt->type) +
    sizeof(pkt->padding_1) +
    sizeof(pkt->padding_2) +
    sizeof(pkt->padding_3) +
    sizeof(pkt->padding_4) +
    sizeof(pkt->padding_5) +
    sizeof(pkt->padding_6) +
    sizeof(pkt->padding_7) +
    sizeof(pkt->padding_8)
  );
}

//===========================================================

//====================Custom CRC Library======================


uint32_t custom_crc32(const uint8_t *data, size_t len) {
  uint32_t crc = 0x00000000;
  
  for (size_t i = 0; i < len; i++) {
    crc ^= data[i];
    for (int j = 0; j < 8; j++) {
      crc = (crc & 1) ? ((crc >> 1) ^ 0x04C11DB7) : (crc >> 1);
    }
  }
  
  return crc;
}
