#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include <Adafruit_NeoPixel.h>

#define LED_COUNT 10
#define PIN_L1 D0
#define PIN_L2 D1
#define PIN_L3 D2

Adafruit_NeoPixel strip1(LED_COUNT, PIN_L1, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel strip2(LED_COUNT, PIN_L2, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel strip3(LED_COUNT, PIN_L3, NEO_GRB + NEO_KHZ800);

Adafruit_MPU6050 mpu;

// --- カスタマイズ設定 ---
float maxGyro = 2.0;      // 感度（小さいほど敏感に反応）
float smoothing = 0.05;   // ★なめらかさ（0.01〜0.1の間で調整。小さいほどゆっくり動く）

// スムーズな値を保存する変数
float smoothX = 0, smoothY = 0, smoothZ = 0;

void setup() {
  Serial.begin(115200);
  if (!mpu.begin()) while (1) delay(10);
  
  strip1.begin(); strip2.begin(); strip3.begin();
  strip1.setBrightness(40); // 電力節約と発熱防止
  strip2.setBrightness(40);
  strip3.setBrightness(40);
}

void loop() {
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  // 現在のジャイロの強さ (0.0 ～ 1.0)
  float rawX = constrain(abs(g.gyro.x) / maxGyro, 0, 1.0);
  float rawY = constrain(abs(g.gyro.y) / maxGyro, 0, 1.0);
  float rawZ = constrain(abs(g.gyro.z) / maxGyro, 0, 1.0);

  // ★ローパスフィルタ：少しずつ目標値に近づける
  smoothX = (rawX * smoothing) + (smoothX * (1.0 - smoothing));
  smoothY = (rawY * smoothing) + (smoothY * (1.0 - smoothing));
  smoothZ = (rawZ * smoothing) + (smoothZ * (1.0 - smoothing));

  // 10段階レベルに変換 (M1～M10)
  int m1 = ceil(smoothX * 10);
  int m2 = ceil(smoothY * 10);
  int m3 = ceil(smoothZ * 10);

  updateLane(strip1, m1, m2, m3, 'R');
  updateLane(strip2, m1, m2, m3, 'G');
  updateLane(strip3, m1, m2, m3, 'B');

  delay(20); // ループを速く回すことで滑らかさアップ
}

void updateLane(Adafruit_NeoPixel &strip, int mx, int my, int mz, char axis) {
  strip.clear();
  int currentM = (axis == 'R') ? mx : (axis == 'G') ? my : mz;

  for (int i = 0; i < currentM; i++) {
    uint8_t r = 0, g = 0, b = 0;
    if (currentM >= 8) {
      float total = (float)mx + my + mz;
      if (total < 0.1) total = 0.1; // ゼロ除算防止
      r = (mx / total) * 255;
      g = (my / total) * 255;
      b = (mz / total) * 255;
    } else {
      if (axis == 'R') r = 255;
      else if (axis == 'G') g = 255;
      else if (axis == 'B') b = 255;
    }
    strip.setPixelColor(i, strip.Color(r, g, b));
  }
  strip.show();
}