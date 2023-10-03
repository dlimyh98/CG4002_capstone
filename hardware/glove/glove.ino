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

const long GYRO_SENSITIVITY = 131;          // Full-scale == +-250deg/s
const long ACCEL_SENSITIVITY = 16384;       // Full-scale == +-2g
const float GYRO_SCALING_FACTOR = 1;        // Gyrometer scaling factor == 131/131 = 1
const float ACCEL_SCALING_FACTOR = 0.03;    // Accelerometer scaling factor == 60/16384 = ~0.03
#define BAUD_RATE 9600
#define SPEC_SHEET_DIFFERENCE 2
#define AVERAGING_COUNTER 500
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

/************************************** AI data collection **************************************/
#ifdef COLLECTING_DATA_FOR_AI
  #define ACCEL_THRESHOLD_FOR_COLLECTION 500
#endif


void setup() {
  Wire.begin();
  Serial.begin(BAUD_RATE);
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
    // Expected to trigger at ~SAMPLING_RATE_FREQUENCY
    get_dmp_data();
  } else {
    // Continuous stream from MPU at ~SAMPLING_RATE_FREQUENCY
    send_to_internal_comms();
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
  //mpu.dmpGetGyro(&raw_gyros, fifoBuffer);
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
  packet.AccX =  IMU.AccX_moving_average_hull * ACCEL_SCALING_FACTOR;
  packet.AccY =  IMU.AccY_moving_average_hull * ACCEL_SCALING_FACTOR;
  packet.AccZ =  IMU.AccZ_moving_average_hull * ACCEL_SCALING_FACTOR;
  packet.GyroX = IMU.GyroX_moving_average_hull * GYRO_SCALING_FACTOR;
  packet.GyroY = IMU.GyroY_moving_average_hull * GYRO_SCALING_FACTOR;
  packet.GyroZ = IMU.GyroZ_moving_average_hull * GYRO_SCALING_FACTOR;
}


void send_to_internal_comms() {
  //see_hma_effectiveness();
      
  // Send over to Internal Comms
  //Serial.write(packet);
  Serial.print(packet.AccX); Serial.print(" ");
  Serial.print(packet.AccY); Serial.print(" ");
  Serial.print(packet.AccZ); Serial.print(" ");
  Serial.print(packet.GyroX); Serial.print(" ");
  Serial.print(packet.GyroY); Serial.print(" ");
  Serial.println(packet.GyroZ);
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
  Serial.print("Raw_Corrected:"); Serial.print(accelerations_corrected.z * SPEC_SHEET_DIFFERENCE); Serial.print(",");
  Serial.print("SMA_Large:"); Serial.print(IMU.AccZ_moving_average_large); Serial.print(",");
  Serial.print("SMA_Small:"); Serial.print(IMU.AccZ_moving_average_small); Serial.print(",");
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

    // PID calibration
    mpu.CalibrateAccel(6);
    mpu.CalibrateGyro(6);

    /*
    Serial.println(IMU.AccX_offset);
    Serial.println(IMU.AccY_offset);
    Serial.println(IMU.AccZ_offset);
    Serial.println(IMU.GyroX_offset);
    Serial.println(IMU.GyroY_offset);
    Serial.println(IMU.GyroZ_offset);
    */
    //mpu.PrintActiveOffsets();

    // DMP is ready
    mpu.setDMPEnabled(true);
    dmpReady = true;
    Serial.println(F("DMP enabled..."));
   
    // get expected DMP packet size for later comparison. Should be 42 (for our DMP version of 2.x)
    // Note that other DMP versions have different FIFO packet size/layout (e.g. DMP version of 6.x has different size & layout)
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