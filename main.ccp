#include <Arduino.h>
#include "HX711.h"

//This value is obtained using the SparkFun_HX711_Calibration sketch
#define LOADCELL_DOUT_PIN  8
#define LOADCELL_SCK_PIN  9
HX711 scale;

#define calibration_factor -400000
void setup() {
  Serial.begin(9600);
  Serial.setTimeout(10);

  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale(calibration_factor); //This value is obtained by using the SparkFun_HX711_Calibration sketch
  scale.tare(); //Assuming there is no weight on the scale at start up, reset the scale to 0  
}

void loop() {  

  if(Serial.available() > 0){
    char input = Serial.read();
    if(input == 's'){
      while (Serial.read() != 'q'){
        int scale_read = abs(int(scale.get_units() * 10000.0)); //scale.get_units() returns a float  
        Serial.println(String(scale_read));
      }
    }
  }
}
