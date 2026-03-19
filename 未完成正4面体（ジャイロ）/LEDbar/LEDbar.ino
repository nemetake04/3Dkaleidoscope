#include <Adafruit_NeoPixel.h>

#define PIN        D0    // 信号線をD3ピンに接続
#define NUMPIXELS  69    // LEDの数に合わせて変更してください

Adafruit_NeoPixel pixels(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  pixels.begin();
}

void loop() {
  // 赤色に光らせる
  colorWipe(pixels.Color(255, 0, 0), 50); 
  // 緑色に光らせる
  colorWipe(pixels.Color(0, 255, 0), 50); 
  // 青色に光らせる
  colorWipe(pixels.Color(0, 0, 255), 50); 
}

// 順番に色を変える関数
void colorWipe(uint32_t color, int wait) {
  for(int i=0; i<pixels.numPixels(); i++) {
    pixels.setPixelColor(i, color);
    pixels.show();
    delay(wait);
  }
}