#include <FastLED.h>

#define LED_PIN     6
#define NUM_LEDS    50
#define BRIGHTNESS  40
#define LED_TYPE    WS2812B
#define COLOR_ORDER GRB
#define TIMEOUT_MS  2000  

CRGB leds[NUM_LEDS];
String mood = "";
unsigned long lastMoodTime = 0;
bool inTimeout = false;

void setup() {
  Serial.begin(115200);
  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);

  fill_solid(leds, NUM_LEDS, CRGB::White);  
  FastLED.show();
  lastMoodTime = millis();  
}

void loop() {
  if (Serial.available()) {
    mood = Serial.readStringUntil('\n');
    mood.trim();
    mood.toUpperCase();  

    showMood(mood);
    lastMoodTime = millis(); 
    inTimeout = false;
  }

  
  if (!inTimeout && millis() - lastMoodTime > TIMEOUT_MS) {
    fill_solid(leds, NUM_LEDS, CRGB::White);
    FastLED.show();
    inTimeout = true;
  }
}

void showMood(String mood) {
  if (mood == "CALM") {
    fill_solid(leds, NUM_LEDS, CRGB::Blue);
  } else if (mood == "FOCUSED") {
    fill_solid(leds, NUM_LEDS, CRGB::Green);
  } else if (mood == "STRESSED") {
    fill_solid(leds, NUM_LEDS, CRGB::Red);
  } else {
    fill_solid(leds, NUM_LEDS, CRGB::Purple);  
  }

  FastLED.show();
}
