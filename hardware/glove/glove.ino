#include <I2Cdev.h>
#include <MPU6050_6Axis_MotionApps20.h>
#include <Wire.h>
#include <CircularBuffer.h>

/**************** https://web.archive.org/web/20191019015332/https://www.i2cdevlib.com/devices/mpu6050#registers (MPU6050 FULL register map) ****************/
/**************** https://www.i2cdevlib.com/docs/html/class_m_p_u6050.html#abd8fc6c18adf158011118fbccc7e7054 (Partial I2Cdev docs) ****************/
#define MPU_ADDRESS 0x68
#define SIGNAL_PATH_RESET 0x68
#define PWR_MGMT_1 0x6B
#define SMPRT_DIV 0x19
#define CONFIG 0x1A
#define GYRO_CONFIG 0x1B
#define ACCEL_CONFIG 0x1C
#define MOT_THR 0x1F
#define MOT_DUR 0x20
#define MOT_DETECT_CTRL 0x69
#define INT_PIN_CFG 0x37
#define INT_ENABLE 0x38

#define BEETLE_INTERRUPT_PIN 2    // D2, INT0
#define INT_STATUS 0x3A
volatile bool is_ZRMOT_interrupt_raised = false;
#define MOT_DETECT_STATUS 0x61

#define ZRMOT_THR 0x21
#define ZRMOT_DUR 0x22
#define ZERO_TO_MOTION 0
#define MOTION_TO_ZERO 1

const long GYRO_SENSITIVITY = 131;
const long ACCEL_SENSITIVITY = 16384;
#define SPEC_SHEET_DIFFERENCE 2
#define AVERAGING_COUNTER 300
#define MOVING_AVERAGE_WINDOW_SIZE 10
#define SQUARE_ROOT_MOVING_AVERAGE_WINDOW_SIZE 3
#define SAMPLING_RATE_FREQUENCY 100

#define COLLECTING_DATA_FOR_AI
//#define NOT_COLLECTING_DATA_FOR_AI

/************************************** MPU control variables (from Jeff Rowberg) **************************************/
MPU6050 mpu;
uint8_t mpuIntStatus;
uint8_t devStatus;           // return status after each device operation (0 = success, !0 = error)
bool dmpReady = false;       // set TRUE if DMP initialization is successful
uint16_t packetSize = 42;    // expected DMP packet size (default is 42 bytes)
uint16_t fifoCount;          // count of all bytes currently in FIFO
uint8_t fifoBuffer[64];      // FIFO storage buffer
volatile bool mpuInterrupt = false;
void dmpDataReady() {
  mpuInterrupt = true;
}

// Orientation/motion vars from DMP
Quaternion q;                         // [w, x, y, z], quaternion container
VectorInt16 raw_accelerations;        // [x, y, z], RAW acceleration readings
VectorFloat gravity;                  // [x, y, z], gravity vector
VectorInt16 accelerations_corrected;  // [x, y, z], acceleration readings adjusted for gravity
VectorInt16 raw_gyros;                // [x,y,z], RAW gyroscope readings

/************************************** IMU 'class' **************************************/
typedef struct s_IMU {
  /**************************** Computing IMU offsets ****************************/
  float AccX, AccY, AccZ;
  float GyroX, GyroY, GyroZ;
  float AccX_offset, AccY_offset, AccZ_offset;
  float GyroX_offset, GyroY_offset, GyroZ_offset;

  /**************************** HULL MOVING AVERAGE ****************************/
  // https://school.stockcharts.com/doku.php?id=technical_indicators:hull_moving_average
  CircularBuffer<long,MOVING_AVERAGE_WINDOW_SIZE/2> AccX_window_small;
  CircularBuffer<long,MOVING_AVERAGE_WINDOW_SIZE/2> AccY_window_small;
  CircularBuffer<long,MOVING_AVERAGE_WINDOW_SIZE/2> AccZ_window_small;
  CircularBuffer<long,MOVING_AVERAGE_WINDOW_SIZE/2> GyroX_window_small;
  CircularBuffer<long,MOVING_AVERAGE_WINDOW_SIZE/2> GyroY_window_small;
  CircularBuffer<long,MOVING_AVERAGE_WINDOW_SIZE/2> GyroZ_window_small;
  bool is_first_time_computing_moving_average_small = true;
  long AccX_moving_average_small = 0, AccY_moving_average_small = 0, AccZ_moving_average_small = 0;
  long GyroX_moving_average_small = 0, GyroY_moving_average_small = 0, GyroZ_moving_average_small = 0;
  int AccX_saved_head_small = 0, AccY_saved_head_small = 0, AccZ_saved_head_small = 0;
  int GyroX_saved_head_small = 0, GyroY_saved_head_small = 0, GyroZ_saved_head_small = 0;

  CircularBuffer<long,MOVING_AVERAGE_WINDOW_SIZE> AccX_window_large;
  CircularBuffer<long,MOVING_AVERAGE_WINDOW_SIZE> AccY_window_large;
  CircularBuffer<long,MOVING_AVERAGE_WINDOW_SIZE> AccZ_window_large;
  CircularBuffer<long,MOVING_AVERAGE_WINDOW_SIZE> GyroX_window_large;
  CircularBuffer<long,MOVING_AVERAGE_WINDOW_SIZE> GyroY_window_large;
  CircularBuffer<long,MOVING_AVERAGE_WINDOW_SIZE> GyroZ_window_large;
  bool is_first_time_computing_moving_average_large = true;
  long AccX_moving_average_large = 0, AccY_moving_average_large = 0, AccZ_moving_average_large = 0;
  long GyroX_moving_average_large = 0, GyroY_moving_average_large = 0, GyroZ_moving_average_large = 0;
  int AccX_saved_head_large = 0, AccY_saved_head_large = 0, AccZ_saved_head_large = 0;
  int GyroX_saved_head_large = 0, GyroY_saved_head_large = 0, GyroZ_saved_head_large = 0;

  CircularBuffer<long,SQUARE_ROOT_MOVING_AVERAGE_WINDOW_SIZE> AccX_window_raw_HMA;
  CircularBuffer<long,SQUARE_ROOT_MOVING_AVERAGE_WINDOW_SIZE> AccY_window_raw_HMA;
  CircularBuffer<long,SQUARE_ROOT_MOVING_AVERAGE_WINDOW_SIZE> AccZ_window_raw_HMA;
  CircularBuffer<long,SQUARE_ROOT_MOVING_AVERAGE_WINDOW_SIZE> GyroX_window_raw_HMA;
  CircularBuffer<long,SQUARE_ROOT_MOVING_AVERAGE_WINDOW_SIZE> GyroY_window_raw_HMA;
  CircularBuffer<long,SQUARE_ROOT_MOVING_AVERAGE_WINDOW_SIZE> GyroZ_window_raw_HMA;
  bool is_first_time_computing_moving_average_hull = true;
  long AccX_moving_average_hull = 0, AccY_moving_average_hull = 0, AccZ_moving_average_hull = 0;
  long GyroX_moving_average_hull = 0, GyroY_moving_average_hull = 0, GyroZ_moving_average_hull = 0;
  long AccX_saved_head_raw_HMA = 0, AccY_saved_head_raw_HMA = 0, AccZ_saved_head_raw_HMA = 0;
  long GyroX_saved_head_raw_HMA = 0, GyroY_saved_head_raw_HMA = 0, GyroZ_saved_head_raw_HMA = 0;

} s_IMU;
s_IMU IMU;

/************************************** Packet for Internal Comms **************************************/
typedef struct __attribute__((packed, aligned(1))) s_packet {
  int8_t AccX, AccY, AccZ;
  int16_t GyroX, GyroY, GyroZ;
} s_packet;
s_packet packet = {0};

/************************************** Buffer for AI data collection **************************************/
#ifdef COLLECTING_DATA_FOR_AI
  #define SAMPLING_WINDOW_SIZE 50
  #define S_PACKET_PACKED_SIZE 9
  #define ACCEL_THRESHOLD_FOR_COLLECTION 500

  s_packet AI_buffer[SAMPLING_WINDOW_SIZE] = {{0}}; // SAMPLING_WINDOW_SIZE can't be too big, Arduino SRAM only has 2048 bytes (and DMP doesn't work above >90% memory usage)
  int8_t gyro_high_reading;                         // Higher 8bits of int16_t Gyro
  int8_t gyro_low_reading;                          // Lower 8bits of int16_t Gyro
  int AI_buffer_index = 0;                          // Index to iterate through AI_buffer array
  bool is_AI_buffer_full = false;                   // Raised when AI_buffer has SAMPLING_WINDOW_SIZE elements stored
#endif


void setup() {
  Wire.begin();
  Serial.begin(9600);
  calibrate_IMU();
  initialize_MPU();
  override_system_configs();                 // Overrides HPF setting and Gyro Sensitivity set by initialize_MPU()
  override_sampling_rate_configs();          // Overrides DLPF bandwidth, Sampling Rate
}


// Internal clock ~8Mhz
void loop() {
  // dmpGetCurrentFIFOPacket() is overflow proof, use it! 
  // Alternative method of polling for INT_STATUS and checking DMP_INT, then reading DMP's FIFO is unreliable (conflicts with Serial.reads())
  if (mpu.dmpGetCurrentFIFOPacket(fifoBuffer)) {
    get_dmp_data();    // Expected to trigger at 100Hz frequency (Sampling Rate)
  } else {
    #ifdef COLLECTING_DATA_FOR_AI
      // Gather SAMPLING_WINDOW_SIZE samples to form a sampling window, then Serial.print() packets over
      if (is_AI_buffer_full) {
        // Iterate through samples in Sample Window
        for (int i = 0; i < SAMPLING_WINDOW_SIZE; i++) {
          // For EACH sample, we retrieve the address of it's packet struct
          int8_t* packet_struct_ptr = (int8_t*) &(AI_buffer[i]);

          // Use the pointer to traverse through the packet struct's elements
          Serial.print("AccX: "); Serial.println(*packet_struct_ptr); packet_struct_ptr += 1;
          Serial.print("AccY: "); Serial.println(*packet_struct_ptr); packet_struct_ptr += 1;
          Serial.print("AccZ: "); Serial.println(*packet_struct_ptr); packet_struct_ptr += 1;

          gyro_low_reading = *packet_struct_ptr; packet_struct_ptr += 1;
          gyro_high_reading = *packet_struct_ptr; packet_struct_ptr += 1;
          Serial.print("GyroX: "); Serial.println( (gyro_high_reading << 8) | gyro_low_reading );

          gyro_low_reading = *packet_struct_ptr; packet_struct_ptr += 1;
          gyro_high_reading = *packet_struct_ptr; packet_struct_ptr += 1;
          Serial.print("GyroY: "); Serial.println( (gyro_high_reading << 8) | gyro_low_reading );

          gyro_low_reading = *packet_struct_ptr; packet_struct_ptr += 1;
          gyro_high_reading = *packet_struct_ptr;
          Serial.print("GyroZ: "); Serial.println( (gyro_high_reading << 8) | gyro_low_reading );          
        }

        // Reset flag
        is_AI_buffer_full = false;
      }
    #endif

    #ifdef NOT_COLLECTING_DATA_FOR_AI
      // Continuous stream from MPU at ~100Hz
      //see_hma_effectiveness();
      
      // Send over to Internal Comms
      //Serial.write(packet);
      Serial.print("IMU.AccX: "); Serial.println(packet.AccX);
      Serial.print("IMU.AccY: "); Serial.println(packet.AccY);
      Serial.print("IMU.AccZ: "); Serial.println(packet.AccZ);
      Serial.print("IMU.GyroX: "); Serial.println(packet.GyroX);
      Serial.print("IMU.GyroY: "); Serial.println(packet.GyroY);
      Serial.print("IMU.GyroZ: "); Serial.println(packet.GyroZ);
    #endif
  }
}


void get_dmp_data() {
  /********************************************* IMPORTANT NOTE *********************************************/
  /* Using i2cdevlib (Jeff Rowberg library), the ACCELEROMETER values are exactly HALF of what you expect
      i.e For default accelerometer sensitivity of +-2g (16384LSB/g sensitivity), and MPU laying down, you would expect ~16834 for Z-axis accel
        However, Jeff Rowberg's library is written with an older spec, which specifies (8192LSB/g) for +-2g. Meaning we get ~8192 for Z-axis accel when MPU laying down
         https://forum.arduino.cc/t/incorrect-accelerometer-sensitivity-with-mpu-6050/461038/17
  */
  mpu.dmpGetQuaternion(&q, fifoBuffer);
  mpu.dmpGetAccel(&raw_accelerations, fifoBuffer);
  mpu.dmpGetGravity(&gravity, &q);
  mpu.dmpGetLinearAccel(&accelerations_corrected, &raw_accelerations, &gravity);

  // For some reason, mpu.dmpGetGyro() is inaccurate (it doesn't tally with sanity_check())
  // We fallback to getRotation, see related https://github.com/jrowberg/i2cdevlib/issues/613
  mpu.getRotation(&(raw_gyros.x), &(raw_gyros.y), &(raw_gyros.z));

  #ifdef COLLECTING_DATA_FOR_AI
    // Thresholding (based on Accelerometer values) for AI data collection
    // For undisturbed MPU, absolute summation across AccX,AccY,AccZ is ~100
    if (abs(accelerations_corrected.x * SPEC_SHEET_DIFFERENCE) 
        + abs(accelerations_corrected.y * SPEC_SHEET_DIFFERENCE) 
        + abs(accelerations_corrected.z * SPEC_SHEET_DIFFERENCE) < ACCEL_THRESHOLD_FOR_COLLECTION)
      return;
  #endif

  // Save HEAD of circular buffer, as push() will cause it to be lost (assuming buffer at full capacity)
  IMU.AccX_saved_head_small = IMU.AccX_window_small.first();
  IMU.AccY_saved_head_small = IMU.AccY_window_small.first();
  IMU.AccZ_saved_head_small = IMU.AccZ_window_small.first();
  IMU.GyroX_saved_head_small = IMU.GyroX_window_small.first();
  IMU.GyroY_saved_head_small = IMU.GyroY_window_small.first();
  IMU.GyroZ_saved_head_small = IMU.GyroZ_window_small.first();
  IMU.AccX_saved_head_large = IMU.AccX_window_large.first();
  IMU.AccY_saved_head_large = IMU.AccY_window_large.first();
  IMU.AccZ_saved_head_large = IMU.AccZ_window_large.first();
  IMU.GyroX_saved_head_large = IMU.GyroX_window_large.first();
  IMU.GyroY_saved_head_large = IMU.GyroY_window_large.first();
  IMU.GyroZ_saved_head_large = IMU.GyroZ_window_large.first();

  // Push SINGLE sample (of different data types) into tail of Circular Buffer
  // Note that accelerations_corrected and raw_gyros IS NOT sensitivity-corrected yet
  IMU.AccX_window_small.push(accelerations_corrected.x * SPEC_SHEET_DIFFERENCE);
  IMU.AccY_window_small.push(accelerations_corrected.y * SPEC_SHEET_DIFFERENCE);
  IMU.AccZ_window_small.push(accelerations_corrected.z * SPEC_SHEET_DIFFERENCE);
  IMU.GyroX_window_small.push(raw_gyros.x);
  IMU.GyroY_window_small.push(raw_gyros.y);
  IMU.GyroZ_window_small.push(raw_gyros.z);
  IMU.AccX_window_large.push(accelerations_corrected.x * SPEC_SHEET_DIFFERENCE);
  IMU.AccY_window_large.push(accelerations_corrected.y * SPEC_SHEET_DIFFERENCE);
  IMU.AccZ_window_large.push(accelerations_corrected.z * SPEC_SHEET_DIFFERENCE);
  IMU.GyroX_window_large.push(raw_gyros.x);
  IMU.GyroY_window_large.push(raw_gyros.y);
  IMU.GyroZ_window_large.push(raw_gyros.z);

  // Compute only iff LARGE window is filled 
  if (IMU.AccX_window_large.isFull()) {
    hull_moving_average();
  }

  // Sensitize and scale up the data (to increase range for AI training)
  const float ACCEL_SCALING_FACTOR = 0.03;    // Accelerometer scaling factor == 60/16384 = ~0.03
  const float GYRO_SCALING_FACTOR = 1;        // Gyrometer scaling factor == 131/131 = 1
  packet.AccX =  IMU.AccX_moving_average_hull * ACCEL_SCALING_FACTOR;
  packet.AccY =  IMU.AccY_moving_average_hull * ACCEL_SCALING_FACTOR;
  packet.AccZ =  IMU.AccZ_moving_average_hull * ACCEL_SCALING_FACTOR;
  packet.GyroX = IMU.GyroX_moving_average_hull * GYRO_SCALING_FACTOR;
  packet.GyroY = IMU.GyroY_moving_average_hull * GYRO_SCALING_FACTOR;
  packet.GyroZ = IMU.GyroZ_moving_average_hull * GYRO_SCALING_FACTOR;

  #ifdef COLLECTING_DATA_FOR_AI
    // Push into our buffer of SAMPLING_WINDOW_SIZE size
    AI_buffer[AI_buffer_index] = packet;

    // Raise flag for saving to .txt file, if our Sampling Window is filled
    if (AI_buffer_index == SAMPLING_WINDOW_SIZE-1) {
      is_AI_buffer_full = true;
      AI_buffer_index = 0;
    } else {
      AI_buffer_index++;
    }
  #endif
}

void hull_moving_average() {
  moving_average_window_small();
  moving_average_window_large();

  IMU.AccX_saved_head_raw_HMA = IMU.AccX_window_raw_HMA.first();
  IMU.AccY_saved_head_raw_HMA = IMU.AccY_window_raw_HMA.first();
  IMU.AccZ_saved_head_raw_HMA = IMU.AccZ_window_raw_HMA.first();
  IMU.GyroX_saved_head_raw_HMA = IMU.GyroX_window_raw_HMA.first();
  IMU.GyroY_saved_head_raw_HMA = IMU.GyroY_window_raw_HMA.first();
  IMU.GyroZ_saved_head_raw_HMA = IMU.GyroZ_window_raw_HMA.first();  

  IMU.AccX_window_raw_HMA.push(2*IMU.AccX_moving_average_small - IMU.AccX_moving_average_large);
  IMU.AccY_window_raw_HMA.push(2*IMU.AccY_moving_average_small - IMU.AccY_moving_average_large);
  IMU.AccZ_window_raw_HMA.push(2*IMU.AccZ_moving_average_small - IMU.AccZ_moving_average_large);
  IMU.GyroX_window_raw_HMA.push(2*IMU.GyroX_moving_average_small - IMU.GyroX_moving_average_large);
  IMU.GyroY_window_raw_HMA.push(2*IMU.GyroY_moving_average_small - IMU.GyroY_moving_average_large);
  IMU.GyroZ_window_raw_HMA.push(2*IMU.GyroZ_moving_average_small - IMU.GyroZ_moving_average_large);

  // Compute only iff LARGE window is filled
  if (IMU.AccX_window_raw_HMA.isFull()) {
    moving_average_window_hull();
  }
}

void moving_average_window_small() {
    if (!IMU.is_first_time_computing_moving_average_small) {
      IMU.AccX_moving_average_small = IMU.AccX_moving_average_small + ( (IMU.AccX_window_small.last() - IMU.AccX_saved_head_small) / (MOVING_AVERAGE_WINDOW_SIZE/2) );
      IMU.AccY_moving_average_small = IMU.AccY_moving_average_small + ( (IMU.AccY_window_small.last() - IMU.AccY_saved_head_small) / (MOVING_AVERAGE_WINDOW_SIZE/2) );
      IMU.AccZ_moving_average_small = IMU.AccZ_moving_average_small + ( (IMU.AccZ_window_small.last() - IMU.AccZ_saved_head_small) / (MOVING_AVERAGE_WINDOW_SIZE/2) );
      IMU.GyroX_moving_average_small = IMU.GyroX_moving_average_small + ( (IMU.GyroX_window_small.last() - IMU.GyroX_saved_head_small) / (MOVING_AVERAGE_WINDOW_SIZE/2) );
      IMU.GyroY_moving_average_small = IMU.GyroY_moving_average_small + ( (IMU.GyroY_window_small.last() - IMU.GyroY_saved_head_small) / (MOVING_AVERAGE_WINDOW_SIZE/2) );
      IMU.GyroZ_moving_average_small = IMU.GyroZ_moving_average_small + ( (IMU.GyroZ_window_small.last() - IMU.GyroZ_saved_head_small) / (MOVING_AVERAGE_WINDOW_SIZE/2) );
  } else {
    IMU.is_first_time_computing_moving_average_small = false;

    for (int i = 0; i < MOVING_AVERAGE_WINDOW_SIZE/2; i++) {
      IMU.AccX_moving_average_small += IMU.AccX_window_small.shift();
      IMU.AccY_moving_average_small += IMU.AccY_window_small.shift();
      IMU.AccZ_moving_average_small += IMU.AccZ_window_small.shift();
      IMU.GyroX_moving_average_small += IMU.GyroX_window_small.shift();
      IMU.GyroY_moving_average_small += IMU.GyroY_window_small.shift();
      IMU.GyroZ_moving_average_small += IMU.GyroZ_window_small.shift();
    }

    IMU.AccX_moving_average_small /= (MOVING_AVERAGE_WINDOW_SIZE/2);
    IMU.AccY_moving_average_small /= (MOVING_AVERAGE_WINDOW_SIZE/2);
    IMU.AccZ_moving_average_small /= (MOVING_AVERAGE_WINDOW_SIZE/2);
    IMU.GyroX_moving_average_small /= (MOVING_AVERAGE_WINDOW_SIZE/2);
    IMU.GyroY_moving_average_small /= (MOVING_AVERAGE_WINDOW_SIZE/2);
    IMU.GyroZ_moving_average_small /= (MOVING_AVERAGE_WINDOW_SIZE/2);
  }
}

void moving_average_window_large() {
    if (!IMU.is_first_time_computing_moving_average_large) {
      IMU.AccX_moving_average_large = IMU.AccX_moving_average_large + ( (IMU.AccX_window_large.last() - IMU.AccX_saved_head_large) / MOVING_AVERAGE_WINDOW_SIZE );
      IMU.AccY_moving_average_large = IMU.AccY_moving_average_large + ( (IMU.AccY_window_large.last() - IMU.AccY_saved_head_large) / MOVING_AVERAGE_WINDOW_SIZE );
      IMU.AccZ_moving_average_large = IMU.AccZ_moving_average_large + ( (IMU.AccZ_window_large.last() - IMU.AccZ_saved_head_large) / MOVING_AVERAGE_WINDOW_SIZE );
      IMU.GyroX_moving_average_large = IMU.GyroX_moving_average_large + ( (IMU.GyroX_window_large.last() - IMU.GyroX_saved_head_large) / MOVING_AVERAGE_WINDOW_SIZE );
      IMU.GyroY_moving_average_large = IMU.GyroY_moving_average_large + ( (IMU.GyroY_window_large.last() - IMU.GyroY_saved_head_large) / MOVING_AVERAGE_WINDOW_SIZE );
      IMU.GyroZ_moving_average_large = IMU.GyroZ_moving_average_large + ( (IMU.GyroZ_window_large.last() - IMU.GyroZ_saved_head_large) / MOVING_AVERAGE_WINDOW_SIZE );
  } else {
    IMU.is_first_time_computing_moving_average_large = false;

    for (int i = 0; i < MOVING_AVERAGE_WINDOW_SIZE; i++) {
      IMU.AccX_moving_average_large += IMU.AccX_window_large.shift();
      IMU.AccY_moving_average_large += IMU.AccY_window_large.shift();
      IMU.AccZ_moving_average_large += IMU.AccZ_window_large.shift();
      IMU.GyroX_moving_average_large += IMU.GyroX_window_large.shift();
      IMU.GyroY_moving_average_large += IMU.GyroY_window_large.shift();
      IMU.GyroZ_moving_average_large += IMU.GyroZ_window_large.shift();
    }
    IMU.AccX_moving_average_large /= MOVING_AVERAGE_WINDOW_SIZE;
    IMU.AccY_moving_average_large /= MOVING_AVERAGE_WINDOW_SIZE;
    IMU.AccZ_moving_average_large /= MOVING_AVERAGE_WINDOW_SIZE;
    IMU.GyroX_moving_average_large /= MOVING_AVERAGE_WINDOW_SIZE;
    IMU.GyroY_moving_average_large /= MOVING_AVERAGE_WINDOW_SIZE;
    IMU.GyroZ_moving_average_large /= MOVING_AVERAGE_WINDOW_SIZE;
  }
}

void moving_average_window_hull() {
    if (!IMU.is_first_time_computing_moving_average_hull) {
      IMU.AccX_moving_average_hull = IMU.AccX_moving_average_hull + ( (IMU.AccX_window_raw_HMA.last() - IMU.AccX_saved_head_raw_HMA) / SQUARE_ROOT_MOVING_AVERAGE_WINDOW_SIZE );
      IMU.AccY_moving_average_hull= IMU.AccY_moving_average_hull + ( (IMU.AccY_window_raw_HMA.last() - IMU.AccY_saved_head_raw_HMA) / SQUARE_ROOT_MOVING_AVERAGE_WINDOW_SIZE );
      IMU.AccZ_moving_average_hull = IMU.AccZ_moving_average_hull + ( (IMU.AccZ_window_raw_HMA.last() - IMU.AccZ_saved_head_raw_HMA) / SQUARE_ROOT_MOVING_AVERAGE_WINDOW_SIZE );
      IMU.GyroX_moving_average_hull = IMU.GyroX_moving_average_hull + ( (IMU.GyroX_window_raw_HMA.last() - IMU.GyroX_saved_head_raw_HMA) / SQUARE_ROOT_MOVING_AVERAGE_WINDOW_SIZE );
      IMU.GyroY_moving_average_hull = IMU.GyroY_moving_average_hull + ( (IMU.GyroY_window_raw_HMA.last() - IMU.GyroY_saved_head_raw_HMA) / SQUARE_ROOT_MOVING_AVERAGE_WINDOW_SIZE );
      IMU.GyroZ_moving_average_hull = IMU.GyroZ_moving_average_hull + ( (IMU.GyroZ_window_raw_HMA.last() - IMU.GyroZ_saved_head_raw_HMA) / SQUARE_ROOT_MOVING_AVERAGE_WINDOW_SIZE );
  } else {
    IMU.is_first_time_computing_moving_average_hull = false;

    for (int i = 0; i < SQUARE_ROOT_MOVING_AVERAGE_WINDOW_SIZE; i++) {
      IMU.AccX_moving_average_hull += IMU.AccX_window_raw_HMA.shift();
      IMU.AccY_moving_average_hull += IMU.AccY_window_raw_HMA.shift();
      IMU.AccZ_moving_average_hull += IMU.AccZ_window_raw_HMA.shift();
      IMU.GyroX_moving_average_hull += IMU.GyroX_window_raw_HMA.shift();
      IMU.GyroY_moving_average_hull += IMU.GyroY_window_raw_HMA.shift();
      IMU.GyroZ_moving_average_hull += IMU.GyroZ_window_raw_HMA.shift();
    }

    IMU.AccX_moving_average_hull /= SQUARE_ROOT_MOVING_AVERAGE_WINDOW_SIZE;
    IMU.AccY_moving_average_hull /= SQUARE_ROOT_MOVING_AVERAGE_WINDOW_SIZE;
    IMU.AccZ_moving_average_hull /= SQUARE_ROOT_MOVING_AVERAGE_WINDOW_SIZE;
    IMU.GyroX_moving_average_hull /= SQUARE_ROOT_MOVING_AVERAGE_WINDOW_SIZE;
    IMU.GyroY_moving_average_hull /= SQUARE_ROOT_MOVING_AVERAGE_WINDOW_SIZE;
    IMU.GyroZ_moving_average_hull /= SQUARE_ROOT_MOVING_AVERAGE_WINDOW_SIZE;
  }
}

void see_hma_effectiveness() {
  Serial.print("Raw_corrected:"); Serial.print(accelerations_corrected.z * SPEC_SHEET_DIFFERENCE); Serial.print(",");
  Serial.print("SMA_10:"); Serial.print(IMU.AccZ_moving_average_large); Serial.print(",");
  Serial.print("SMA_5:"); Serial.print(IMU.AccZ_moving_average_small); Serial.print(",");
  Serial.print("HMA:"); Serial.println(IMU.AccZ_moving_average_hull);
}

void read_sensors() {
   Serial.print("AccX:"); Serial.println(packet.AccX);
   Serial.print("AccY:"); Serial.println(packet.AccY);
   Serial.print("AccZ:"); Serial.println(packet.AccZ);
   Serial.print("GyroX:"); Serial.println(packet.GyroX);
   Serial.print("GyroY:"); Serial.println(packet.GyroY);
   Serial.print("GyroZ:"); Serial.println(packet.GyroZ);
}

void initialize_MPU() {
  mpu.initialize();
  Serial.println(mpu.testConnection() ? F("MPU6050 connection successful") : F("MPU6050 connection failed"));

  /************************* Initialize DMP within the MPU6050 *************************/
  devStatus = mpu.dmpInitialize();

  // Check if DMP connection succeeded
  if (devStatus == 0) {
    // Input the offsets we calculated, for calibration (note that these are RAW offsets, not sensitivity-scaled yet)
    mpu.setXAccelOffset(IMU.AccX_offset);
    mpu.setYAccelOffset(IMU.AccY_offset);
    mpu.setZAccelOffset(IMU.AccZ_offset);
    mpu.setXGyroOffset(IMU.GyroX_offset);
    mpu.setYGyroOffset(IMU.GyroY_offset);
    mpu.setZGyroOffset(IMU.GyroZ_offset);

    // Enable Interrupts (optional)
    //attachInterrupt(digitalPinToInterrupt(BEETLE_INTERRUPT_PIN), dmpDataReady, RISING);

    // Calibrate
    mpu.CalibrateAccel(6);
    mpu.CalibrateGyro(6);
    mpu.PrintActiveOffsets();

    // DMP is ready
    mpu.setDMPEnabled(true);
    dmpReady = true;
    Serial.println(F("DMP enabled..."));
   
    // get expected DMP packet size for later comparison
    packetSize = mpu.dmpGetFIFOPacketSize();
  } else {
    // ERROR!
    Serial.print(F("DMP Initialization failed (code "));
    Serial.print(devStatus);
    Serial.println(F(")"));
  }

}

void override_system_configs() {  
  /************************************************* POWER, SIGNALS (done in mpu.initialize()) ************************************************/
  //register_write(MPU_ADDRESS, SIGNAL_PATH_RESET, 0x7);         // Reset analog & digital signal paths for Gyro, Accelerometer, Temp
  //register_write(MPU_ADDRESS, PWR_MGMT_1, 0x0);                // Put MPU6050 OUT of sleep-mode (DO NOT USE DEVICE_RESET[7], it bugs out somehow)

  /*********************************************************** ACCELERATION, GYROSCOPE ***********************************************************/
  // https://www.researchgate.net/publication/224331816_A_New_PCB-Based_Low-Cost_Accelerometer_for_Human_Motion_Sensing#pf1
  // Public Domain Dataset for Human Activity Recognition using Smartphones - ESANN 2013, European Symposiumon Artificial Neural Networks
  register_write(MPU_ADDRESS, ACCEL_CONFIG, 0x4);      // default [4:3]AFS_SEL (stick to default +-2g for now) 
                                                       // and [2:0]ACCEL_HPF of ~0.625Hz HPF
                                                       // if HPF set to HOLD, gravity is removed from threshold calculations. But we won't see the difference when directly reading from Accelerometer
  register_write(MPU_ADDRESS, GYRO_CONFIG, 0x0);       //  default [4:3]FS_SEL, for now we stick to default Gyroscope value of +- 250deg/s
}

void override_sampling_rate_configs() {
  // https://www.researchgate.net/publication/224331816_A_New_PCB-Based_Low-Cost_Accelerometer_for_Human_Motion_Sensing#pf1
  // Public Domain Dataset for Human Activity Recognition using Smartphones - ESANN 2013, European Symposiumon Artificial Neural Networks
  /************************ 
  Accelerometer/Gyroscope ------> MPU6050 DMP ------> External
  ***********************/
  register_write(MPU_ADDRESS, SMPRT_DIV, (1000/SAMPLING_RATE_FREQUENCY)-1);   // Accelerometer & Gyroscope Sampling Rate has baseline of 1KHz (if you modify SMPRT_DIV from default)
  register_write(MPU_ADDRESS, CONFIG, 3);                                     // sets [2:0]DLPF_CFG bits (configures Low-pass filter to below settings)

  /********************* Accelerometer *********************/
  // Use serial plotter to determine when movement starts and stop
  // Sampling frequency = 100Hz
  // DLPF = 44Hz
  // Delay = 4.9ms

  /********************* Gyroscope *********************/
  // Sampling frequency = 100Hz
  // DLPF = 44Hz
  // Delay = 4.9ms
}

void calibrate_IMU() {
  // Zero out all offsets
  IMU.AccX_offset = 0, IMU.AccY_offset = 0, IMU.AccZ_offset = 0;
  IMU.GyroX_offset = 0, IMU.GyroY_offset = 0, IMU.GyroZ_offset = 0;
  calculate_average_offset();

  /*
  Serial.print("AccX_offset: "); Serial.println(IMU.AccX_offset);
  Serial.print("AccY_offset: "); Serial.println(IMU.AccY_offset);
  Serial.print("AccZ_offset: "); Serial.println(IMU.AccZ_offset);
  Serial.print("GyroX_offset: "); Serial.println(IMU.GyroX_offset);
  Serial.print("GyroY_offset: "); Serial.println(IMU.GyroY_offset);
  Serial.print("GyroZ_offset: "); Serial.println(IMU.GyroZ_offset);
  */
}

void calculate_average_offset() {
  int i = 0;
  float AccX_offset_culmative = 0, AccY_offset_culmative = 0, AccZ_offset_culmative = 0;
  float GyroX_offset_culmative = 0, GyroY_offset_culmative = 0, GyroZ_offset_culmative = 0;

  while (i < AVERAGING_COUNTER) {
    read_raw_IMU();

    AccX_offset_culmative = AccX_offset_culmative + IMU.AccX;
    AccY_offset_culmative = AccY_offset_culmative + IMU.AccY;
    AccZ_offset_culmative = AccZ_offset_culmative + IMU.AccZ;
    GyroX_offset_culmative = GyroX_offset_culmative + IMU.GyroX;
    GyroY_offset_culmative = GyroY_offset_culmative + IMU.GyroY;
    GyroZ_offset_culmative = GyroZ_offset_culmative + IMU.GyroZ;
    i++;
  }

  // Average out the errors
  IMU.AccX_offset = AccX_offset_culmative / AVERAGING_COUNTER;
  IMU.AccY_offset = AccY_offset_culmative / AVERAGING_COUNTER;
  IMU.AccZ_offset = AccZ_offset_culmative / AVERAGING_COUNTER;
  IMU.GyroX_offset = GyroX_offset_culmative / AVERAGING_COUNTER;
  IMU.GyroY_offset = GyroY_offset_culmative / AVERAGING_COUNTER;
  IMU.GyroZ_offset = GyroZ_offset_culmative / AVERAGING_COUNTER;


  // Formula at (https://web.archive.org/web/20190515215636/https://www.nxp.com/files-static/sensors/doc/app_note/AN3461.pdf)
  // roll_error = roll_error + ((atan((AccY) / sqrt(pow((AccX), 2) + pow((AccZ), 2))) * 180 / PI)); 
  // pitch_error = pitch_error + ((atan(-1 * (AccX) / sqrt(pow((AccY), 2) + pow((AccZ), 2))) * 180 / PI));
}

void read_raw_IMU() {
  /********************************** Read accelerometer values (ACCEL_XOUT_H, ACCEL_XOUT_L, ..., ACCEL_ZOUT_L) **********************************/
  Wire.beginTransmission(MPU_ADDRESS);
  Wire.write(0x3B);                             // ACCEL_XOUT_H register
  Wire.endTransmission(false);                  // do not release the I2C bus 
  Wire.requestFrom(MPU_ADDRESS, 6, false);      // request 6 bytes

  IMU.AccX = (Wire.read() << 8 | Wire.read());
  IMU.AccY = (Wire.read() << 8 | Wire.read());
  IMU.AccZ = (Wire.read() << 8 | Wire.read());

  Wire.beginTransmission(MPU_ADDRESS);
  Wire.write(0x43);                              // GYRO_XOUT_H register
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDRESS, 6, true);

  IMU.GyroX = (Wire.read() << 8 | Wire.read());
  IMU.GyroY = (Wire.read() << 8 | Wire.read());
  IMU.GyroZ = (Wire.read() << 8 | Wire.read());
}

void register_write(uint8_t MPU_address, uint8_t register_address, uint8_t value_to_write) {
  // I2C protocol
  Wire.beginTransmission(MPU_ADDRESS);           // Start communication with MPU (I2C address of 0x68)
  Wire.write(register_address);                  // Access some register of MPU
  Wire.write(value_to_write);                    // Write some value to register
  Wire.endTransmission(false);          // End the transmission (send bytes over I2C protocol), 
                                        // but restart signal will be resent (i.e. prevents another Master device from transmitting between messages)
}

uint8_t register_read(uint8_t MPU_address, uint8_t register_address) {
  // I2C protocol
  uint8_t data;
  Wire.beginTransmission(MPU_ADDRESS);                    // Start communication with MPU (I2C address of 0x68)
  Wire.write(register_address);                           // Access some register of MPU
  Wire.endTransmission(false);                            // End the transmission (send bytes over I2C protocol), 
                                                          // but restart signal will be resent (i.e. prevents another Master device from transmitting between messages)
  Wire.requestFrom(MPU_address, (uint8_t) 1);             // Request ONE byte
  data = Wire.read();
  return data;
}

void sanity_check() {
  float AccX, AccY, AccZ, Tmp;
  float GyroX, GyroY, GyroZ;
  Wire.beginTransmission(MPU_ADDRESS);
  Wire.write(0x3B);  // starting with register 0x3B (ACCEL_XOUT_H)
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDRESS,14,true);  // request a total of 14 registers
  AccX=Wire.read()<<8|Wire.read();  // 0x3B (ACCEL_XOUT_H) & 0x3C (ACCEL_XOUT_L)    
  AccY=Wire.read()<<8|Wire.read();  // 0x3D (ACCEL_YOUT_H) & 0x3E (ACCEL_YOUT_L)
  AccZ=Wire.read()<<8|Wire.read();  // 0x3F (ACCEL_ZOUT_H) & 0x40 (ACCEL_ZOUT_L)
  Tmp=Wire.read()<<8|Wire.read();  // 0x41 (TEMP_OUT_H) & 0x42 (TEMP_OUT_L)
  GyroX=Wire.read()<<8|Wire.read();  // 0x43 (GYRO_XOUT_H) & 0x44 (GYRO_XOUT_L)
  GyroY=Wire.read()<<8|Wire.read();  // 0x45 (GYRO_YOUT_H) & 0x46 (GYRO_YOUT_L)
  GyroZ=Wire.read()<<8|Wire.read();  // 0x47 (GYRO_ZOUT_H) & 0x48 (GYRO_ZOUT_L)
  Serial.print("AccX = "); Serial.print(AccX);
  Serial.print(" | AccY = "); Serial.print(AccY);
  Serial.print(" | AccZ = "); Serial.print(AccZ);
  Serial.print(" | Tmp = "); Serial.print(Tmp/340.00+36.53);  //equation for temperature in degrees C from datasheet
  Serial.print(" | GyroX = "); Serial.print(GyroX);
  Serial.print(" | GyroY = "); Serial.print(GyroY);
  Serial.print(" | GyroZ = "); Serial.println(GyroZ);
  delay(333);
}

void configure_zero_motion_interrupt() {
  int counter = 0;
  float AccX_recorded = 0, AccY_recorded = 0, AccZ_recorded = 0;
  float GyroX_recorded = 0, GyroY_recorded = 0, GyroZ_recorded = 0;
  bool is_fresh_data = false;
  /*********************************************************** CONFIGURE MOTION INTERRUPT ***********************************************************/
  // 1. Determine the detection threshold for zero motion interrupt generation. Units for ZRMOT_THR is 1LSB/2mg.
  //    - ZRMOT is detected when absolute value of accelerometer for THREE axes are EACH less than the ZRMOT_THR amount.
  //    - If the above condition is met, the ZRMOT_DUR counter is incremented
  //    - ZRMOT interrupt is raised when ZRMOT_DUR counter reaches the value we specify in ZRMOT_DUR

  /* Unlike Free Fall or Motion detection, Zero Motion detection triggers an
   * interrupt both when Zero Motion is first detected and when Zero Motion is no longer detected.

   * When a zero motion event is detected, a Zero Motion Status will be indicated in MOT_DETECT_STATUS register (Register 0x61). 
   * When a motion-to-zero-motion condition is detected, the status bit is set to 1. 
   * When a zero-motion-to-motion condition is detected, the status bit is set to 0.*/
  register_write(MPU_ADDRESS, ZRMOT_THR, 35);        // ZRMOT acceleration threshold set at (NUMBER * 2)

  // 2. ZRMOT_DUR ticks at 16Hz (1LSB/64ms), and continually increments when ZRMOT_THR threshold is exceeded by ALL three accelerometer axes.
  //    When ZRMOT_DUR's counter exceeds ZRMOT_DUR's threshold, we raise zero-motion detection interrupt
  register_write(MPU_ADDRESS, ZRMOT_DUR, 1);        // Time threshold is set at (NUMBER * 2)

  // 3. Other configurations for motion detection, namely...
  //    - [5:4]ACCEL_ON_DELAY, specifies additional power-on delay for Accelerometer.
  //        - We add 1ms to the default power-on delay of 4ms
  //    - [3:2]FF_COUNT, configures Free-fall detection counter DECREMENT rate.
  //        - Unused for us.
  //    - [1:0]MOT_COUNT, configures Motion detection counter DECREMENT rate.
  //        - Unused for us.
  register_write(MPU_ADDRESS, MOT_DETECT_CTRL, 0x10);

  // 4. Configure interrupt pin (INT of MPU6050, NOT the Beetle's interrupt pin)
  //      - INT_LEVEL[7], INT pin is active-low
  //      - LATCH_INT_EN[5], INT pin emits 50us pulse when triggered
  register_write(MPU_ADDRESS, INT_PIN_CFG, 128);
}

void zero_motion_method() {
  //pinMode(BEETLE_INTERRUPT_PIN, INPUT_PULLUP);                                              // D2(INT0) is active-low interrupt pin
  //attachInterrupt(digitalPinToInterrupt(BEETLE_INTERRUPT_PIN), beetle_ISR_func, FALLING);   // D2 runs beetle_ISR_func() whenever it goes from HIGH->LOW 
  //register_write(MPU_ADDRESS, INT_ENABLE, 0x20);

  /*
  Wire.beginTransmission(MPU_ADDRESS);
  Wire.write(MOT_DETECT_STATUS);                      
  Wire.endTransmission(false);                        // do not release the I2C bus 
  Wire.requestFrom(MPU_ADDRESS, 1, false);            // request 1 byte
  int zero_motion_binary = Wire.read();

  if (zero_motion_binary == ZERO_TO_MOTION) {
    // Begin recording data
    is_fresh_data = true;
    read_sensitize_IMU();

    AccX_recorded = AccX_recorded + (IMU.AccX - IMU.AccX_offset);
    AccY_recorded = AccY_recorded + (IMU.AccY - IMU.AccY_offset);
    AccZ_recorded = AccZ_recorded + (IMU.AccZ - IMU.AccZ_offset);

    GyroX_recorded = GyroX_recorded + (IMU.GyroX - IMU.GyroX_offset);
    GyroY_recorded = GyroY_recorded + (IMU.GyroY - IMU.GyroY_offset);
    GyroZ_recorded = GyroZ_recorded + (IMU.GyroZ - IMU.GyroZ_offset);

    counter++;
  } else {
    if (is_fresh_data) {
      // We just completed a motion, thus we have some motion data to process

      if (counter >= 100) {
        // If motion is above threshold period of time, we consider it valid
        packet.AccX = (int8_t) (AccX_recorded*ACCEL_SCALING / counter);
        packet.AccY = (int8_t) (AccY_recorded*ACCEL_SCALING / counter);
        packet.AccZ = (int8_t) (AccZ_recorded*ACCEL_SCALING / counter);

        packet.GyroX = (int16_t) (GyroX_recorded*GYRO_SCALING / counter);
        packet.GyroY = (int16_t) (GyroY_recorded*GYRO_SCALING / counter);
        packet.GyroZ = (int16_t) (GyroZ_recorded*GYRO_SCALING / counter);

        Serial.print("Samples taken: "); Serial.println(counter);
        Serial.print("packet.AccX: "); Serial.println(packet.AccX);
        Serial.print("packet.AccY: "); Serial.println(packet.AccY);
        Serial.print("packet.AccZ: "); Serial.println(packet.AccZ);
        Serial.print("packet.GyroX: "); Serial.println(packet.GyroX);
        Serial.print("packet.GyroY: "); Serial.println(packet.GyroY);
        Serial.print("packet.GyroZ: "); Serial.println(packet.GyroZ);
      }

      // Irregardless if valid or junk data, we reset the variables used for collecting data
      is_fresh_data = false;
      counter = 0;
      AccX_recorded = AccY_recorded = AccZ_recorded = 0;
      GyroX_recorded = GyroY_recorded = GyroZ_recorded = 0;
    }
  }*/
}