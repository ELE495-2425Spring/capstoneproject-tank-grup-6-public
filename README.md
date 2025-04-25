# TOBB ETÜ ELE495 - Capstone Project

# Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Screenshots](#screenshots)
- [Acknowledgements](#acknowledgements)

## Introduction
This project aims to enable an autonomous vehicle to detect the location of an antenna broadcasting on the 433MHz band with the help of YTR (Yet Another Tracking Receiver) and navigate towards it.

Youtube Video Link : https://youtu.be/4y7KAGOcsKI

## Features
- Autonomous Signal Tracking: The vehicle autonomously tracks the 433MHz signal using YTR and locates the antenna, stopping autonomously when it is within 70cm of the transmitter.
- Real-time User Interface: A user interface displays the vehicle’s real-time heading, position, and signal strength (dB).
- Time Efficiency: The vehicle reaches the transmitter's location within 2 minutes.
## Hardware
- Raspberry Pi 4 Model B, Arduino Nano, 433MHz Yagi-Uda Antenna, 433MHz Omnidirectional Antenna, RTL-SDR, SMA Connector, Coaxial Cable (50 Ohm), Li-ion Batteries (3 units), Power Bank (20W Output Power), Motor Driver (L298N), Car Kit, Accelerometer.
- Raspberry Os
## Applications:
  - Autonomous Navigation: Can be used in autonomous vehicles or robots for precise navigation based on signal detection and tracking.
  - Signal Detection and Localization: Ideal for applications in search and rescue, where finding a specific signal or transmitter is crucial.
  -Wireless Communication Testing: Useful for testing and measuring signal strength in different environments for wireless communication systems.
  -Antenna Positioning: Can be employed in antenna alignment and positioning applications to optimize signal reception or broadcasting.
## Services 
- Custom Signal Tracking Solutions: Provide tailored signal tracking systems for various industries, including telecommunications and security.
- Autonomous System Integration: Integrate autonomous vehicle control systems for navigation based on signal tracking for research or commercial applications.
- Signal Strength Monitoring: Offer real-time monitoring services for signal strength measurement across large areas or specific zones.

## Installation
- Install Raspberry Pi OS.
- Assign pins for the motor driver and accelerometer on the Raspberry Pi.
- Assemble the vehicle kit with Raspberry Pi, motor driver, accelerometer, and power bank.
- Build a Yagi-Uda antenna suitable for 433MHz.
- The dimensions of the Yagi-Uda antenna are provided in the image below.
- Mount the antenna on the car’s top parallel to the ground. Solder one half of the dipole to the positive side of the coaxial cable and the other half to the ground side.
- Install the Raspberry Pi RTL-SDR library and retrieve the algorithm from main.py.
- Perform tests by transmitting on 433MHz using the Arduino Nano and the omnidirectional antenna.
- Create the user interface.



## Usage
Install Required Libraries before running the project, make sure all necessary dependencies are installed on your Raspberry Pi. pyrtlsdr, smbus2, Rpi.GPIO.
Connect the Raspberry Pi and motor driver to the vehicle kit.
Assemble the Yagi-Uda antenna as per the provided dimensions.
Ensure the 433MHz RTL-SDR is properly connected and configured.
To start the tracking process, execute the main Python file:

bash
streamlit run main.py
The vehicle will begin searching for the 433MHz signal. It will rotate 360 degrees, measuring signal strength and moving towards the direction of the highest signal.

The real-time user interface will display on your Raspberry Pi screen, showing:

Vehicle’s current position and heading.
Signal strength (in dB).
The vehicle will autonomously stop once it reaches within 70cm of the transmitter.

If you need to stop the vehicle manually at any point, press CTRL+C in the terminal.

## Yagi-Uda Antenna :


| Parts   | Length (cm) | Distance (cm) |
|----------|------------|-------------|
| Reflector (R) | 34.5 | 0 |
| Dipol (A) | 33.5 | 13.5 |
| Director 1 (D1) | 30.5 | 23.2 |
| Director 2 (D2) | 30.5 | 36.7 |
| Director 3 (D3) | 30.5 | 50.2 |

## Screenshots
![YagiUda_Anten_433Mhz](https://github.com/user-attachments/assets/a31aa550-d301-43c3-aeca-83812927e940)
 
![Autonomous Car](https://github.com/user-attachments/assets/ea91f331-1156-4ede-abb7-06f21883966d)

![Graphical User Interface](https://github.com/user-attachments/assets/e4eafbe1-51f7-4bac-aa9a-7461e6b8b237)



## Acknowledgements
Raspberry Pi Foundation, RTL-SDR Project, Yagi-Uda Antenna Design Resources, Open-Source Community. 

[Resource]https://www.raspberrypi.org/  
[Resource]https://www.rtl-sdr.com/  
[Resource]https://www.arduino.cc/  
[Resource]https://en.wikipedia.org/wiki/Yagi-Uda_antenna  
[Contributor 1](https://github.com/SirAlperen)
[Contributor 2](https://github.com/user1)
[Contributor 3](https://github.com/user1)
[Contributor 4](https://github.com/user1)
[Contributor 5](https://github.com/user1)

## TÜRKÇE 
# Ele495-6 | Otonom Araba ile 433Mhz Anten Takibi
Bu proje, otonom bir aracın YTR yardımıyla  433MHz bandında yayın yapan bir antenin konumunu tespit edip ona doğru yönlenmesini sağlamayı amaçlamaktadır.

**Projedeki Hedefler**  
- Aracın YTR kullanarak Otonom Şekilde 433Mhz'deki Sinyali Takip edip anteni bulması ve 70cm'den az yaklaştığında otonom şekilde durması.
-  Kullanıcı arayüzünün oluşturulması ve bu arayüzde aracın anlık yön,konum ve sinyalin genliği(dB)'nin gösterilmesi.
-   Araç Vericinin Konumuna 2 dakika içerisinde ulaşmalıdır.
-   Tüm Malzemeler KDV dahil 10.000 TL'yi aşmamalıdır. 

**Projenin donanım gereksinimleri**  
Raspberry Pi 4 Model B, Arduino Nano, 433Mhz Yagi-Uda Anten, 433Mhz Yönsüz Anten, Rtl-Sdr, Sma Konnektör ve Koaksiyel kablo(50 Ohm), Li-ion pil(3 adet), Powerbank(20W Çıkış Güçlü), Motor Sürücü(L298N), Araba kiti, ivmeölçer.

**Projenin Yapılması İçin İzlenmesi Gereken Adımlar**  
- Raspberry Pi OS'in kurulması.  
- Raspberry Pi üzerinden Motor sürücü ve ivmeölçer için pinlerin belirlenip atanması. 
- Araç Kitinin, Raspberry Pi, Motor Sürücü, ivmeölçer ve powerbank ile birleştirilmesi.
- 433Mhz'e uygun Yagi-Uda Antenin Yapılması.
  - Yagi-Uda Anten için ölçüler aşağıdaki fotoğrafta belirtilmiştir.
- Antenin Arabanın üstüne yere paralel şekilde montajlanması. Dipol kısmın yarısının koaksiyel kablonun + kısmına lehim yapılması, diğer yarısının koaksiyel kablonun toprak kısmına lehimlenmesi.
- Raspberry Pi Rtl-Sdr Kütüphanesinin kurulması ve algoritmanın main.py'dan alınması.
- Teslerin Yapılabilmesi için Ardino Nano ve Yönsüz anten kullanılarak  433Mhz'de Yayım yapılması.
- Kullanıcı Arayüzünün Oluşturulması

**Kodun Çalışma Mantığı**  
Otonom Araba bulunduğu noktada 360 derece dönerek 433Mhz'de sinyalin gücünü her bir 30 derece için kaydediyor. 360 derece tamamlandıktan sonra sinyal gücünün en yüksek olduğu açıya dönüp belirli bir mesafe düz ilerliyor. Sonrasında üstteki adımı tekrarlayarak iki veya üç iterasyonda(Mesafeye bağlı olarak)) vericinin yanına 70cm'den kısa olacak şekilde ulaşıyor. 

**Kodların Açıklanması**
- **main.py :** Ana kontrol kodu. Programın ana döngüsünü içerir ve kullanılan fonksiyonlar burada tanımlı değil.
- **araba_kontrol_pid.py  :** Aracın Yönlendirme Kodlarının Olduğu Dizin. Bu dizinde Aracın PID kontrol ile ileri,geri gitmesini ve istenilen açıda sağa ve sola dönmesini sağlayan fonksiyonlar bulunuyor. Bu Fonkisyonlar sağlanmasını sağlayan alt fonksiyonların bulunduğu dosyalar ise :
  - gyro_noth.py → İvmeölçer ve yön belirleme
- **signal_olcum.py :** Yazılım Tabanlı Radyonun Kodlarının bulunduğu dizin. Bu dizinde Rtl-Sdr'ın aktif hale getirilmesi, istenilen frekansta istenilen örnekleme hızında ve istenilen kazanç değerinde sinyalin gücünün ölçülmesi sağlanıyor. Sinyalinin gücünü ölçerken Fast Fourier Transform kullanıldı. Bu dizin sayesinde Sinyalin Spekturumu elde edildi.

**Sonuçlar**   
Otonom Araç Yüksek olasılıkla vericinin bulunduğu konuma yüksek hassasiyetle ulaşabiliyor. Ancak Etrafta Bulunan yansıtıcı yüzeylerin bulunduğu bazı kısımlarda olduğundan daha yüksek güçte ölçümler görüldü. Bu yüksek güçte ölçümler bazen yayım yapan antenin olduğu yönden bile daha fazla gözüktüğü için otonom arabanın yoldan saptığı senaryolar gözlemlendi. Aracın Vericinin yanına 70cm'den kısa mesafe yaklaştığında durması için bir eşik değeri atandı ve alınan sinyal gücü bu değere eşit veya yüksek olduğunda araç otonom olarak durarak bulma işlemini tamamlıyor.








