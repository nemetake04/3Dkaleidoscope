#include <WiFiS3.h>

// ===== ここだけ変更 =====
char ssid[] = "musiclab";
char pass[] = "soundnet";
// ========================

int status = WL_IDLE_STATUS;

void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println("=== BOOT ===");

  // WiFiモジュール確認
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("WiFi module not found");
    while (true);
  }

  Serial.print("Connecting to ");
  Serial.println(ssid);

  // 接続
  while (status != WL_CONNECTED) {
    status = WiFi.begin(ssid, pass);
    delay(1000);
    Serial.print(".");
  }

  Serial.println("\nWiFi CONNECTED");

  IPAddress ip = WiFi.localIP();
  Serial.print("IP ADDRESS: ");
  Serial.println(ip);
}

void loop() {
  // 何もしない
}
