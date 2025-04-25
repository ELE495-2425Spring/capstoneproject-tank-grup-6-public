import time
import logging
import numpy as np
import rtlsdr
import streamlit as st
import matplotlib.pyplot as plt
from Navigate.araba_kontrol_pid import Araba
from Navigate.gyro_noth import GyroSensor2
from Signal.signal_olcum import (
    measure_signal_power_narrow,
    measure_signal_power_wide,
    measure_signal_power_narrow_rtlsdr,
    measure_signal_power_wide_rtlsdr,
    get_signal_strength
)


# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Initialize session state at module level
if 'running' not in st.session_state:
    st.session_state.running = False
if 'stop' not in st.session_state:
    st.session_state.stop = False

def run_navigation():
    try:
        # Initialize components
        gyro = GyroSensor2()
        nav = Araba()
        sdr = rtlsdr.RtlSdr()
        sdr.sample_rate = 2.048e6
        sdr.center_freq = 433e6
        sdr.gain = 0

        # Parameters
        stop_treshold = 11  # Adjusted to a realistic value (was 100 dBm)
        donen_aci = 30
        turns_per_loop = 12
        turn_angle = 20
        aci = 0
        best_aci = 0
        prev_aci = 0
        rotate_duty_cycle = 90 #80
        forward_duty_cycle = 70
        for_dur = 2.5
        max_index = 0

        # Streamlit placeholders
        status_text = st.empty()
        angle_box = st.empty()
        power_box = st.empty()  # For Anlık Ölçülen Güç
        reached_box = st.empty()  # For Konuma Ulaşıldı
        spectrum_plot = st.empty()  # For spectrum graph

        # Update status
        status_text.write("Araba Çalışıyor...")
         
        # 1. İTERASYON 360 DERECE
        for loop in range(1):

            #Durdur Butonunun Çalışması :
            if st.session_state.stop:
                logger.info("Navigation stopped by user")
                break

            avg_powers = []
            found_flag = False

            # Arama Fazı, Sağa Dönerek Ölçümler Alıyor
            for i in range(turns_per_loop):     

                #Arayüze Açının Bastırılması
                angle_box.markdown(
                    f'<div style="border: 2px solid #4CAF50; padding: 10px; border-radius: 5px; text-align: center;">'
                    f'<b>Şu anki yön</b>: {aci:.2f}°<br><b>En iyi Yön</b>: {(best_aci):.2f}°</div>',
                    unsafe_allow_html=True
                )

                #Sinyallerin hesaplanması:
                latest_power_dbm = get_signal_strength(sdr)
                frequencies, powers = measure_signal_power_wide_rtlsdr(sdr)
                avg_powers = np.append(avg_powers, latest_power_dbm)
                avg_powers = np.array(avg_powers)

                #Arayüze Gücün ve Grafiğin Bastırılması::
                power_box.markdown(
                    f'<div style="border: 2px solid #2196F3; padding: 10px; border-radius: 5px; text-align: center;">'
                    f'<b>Anlık Ölçülen Güç</b>: {latest_power_dbm if latest_power_dbm is not None else "N/A"} dBm</div>',
                    unsafe_allow_html=True
                )
                if powers is not None:
                    fig, ax = plt.subplots()
                    ax.plot(frequencies, powers, label="Signal Power")
                    ax.set_xlabel("Frequency (MHz)")
                    ax.set_ylabel("Power (dBm)")
                    # ax.set_ylim(60, -10)
                    ax.set_title("Spectrum (432–434 MHz)")
                    ax.set_xlim(432e6, 434e6)
                    ax.grid(True)
                    ax.legend()
                    spectrum_plot.pyplot(fig)
                    plt.close(fig)
                if powers is None:
                    logger.error("Failed to measure signal power, skipping")
                    continue

                # Açı ve DBM'in terminale bastırılması.
                logger.info("Turn %d: %.5f dBm, Angle: %.2f°", i, latest_power_dbm, aci)

                
                #Sağa Dönmenin Yapılması
                if i != turns_per_loop-1 :  #11  yani 11 kez dönüyor : 0 30 60 90 120 180 210 240 270 300 330 360
                    max_index = avg_powers.argmax() # Dizideki GÜçlerin Sıralanması
                    best_aci = (donen_aci*max_index)%360
                    aci = (aci + donen_aci)%360
                    nav.saga_don(gyro, turn_angle, max_duty=rotate_duty_cycle)
                    time.sleep(0.5)
        
            #Max İndexin Bulunması Sola Dönme Sayısının Belirlenmesi ve Uygulanması
            max_index = avg_powers.argmax() 
            left_turns_needed = 11 - max_index 
            for j in range(left_turns_needed):
                aci = (donen_aci*max_index) % 360
                best_aci = aci
                nav.sola_don(gyro, turn_angle, max_duty=rotate_duty_cycle)
                time.sleep(0.05)

        logger.info("Max signal at index %d, angle %.2f°, turning left %d times, after that moving forward",
        max_index, best_aci, left_turns_needed)        
        nav.ileri(for_dur-0.25, duty_cycle=forward_duty_cycle)
        time.sleep(0.25)

        #Arabanın 90 derece sağa dönmesi
        for k in range (3):
            aci = (aci + donen_aci)%360
            nav.saga_don(gyro, turn_angle, max_duty = rotate_duty_cycle)
            logger.info(" ARABA 90 DERECE SAĞA DÖNECEK : Turn %d: Angle: %.2f°", k, aci)
            angle_box.markdown(
                    f'<div style="border: 2px solid #4CAF50; padding: 10px; border-radius: 5px; text-align: center;">'
                    f'<b>Şu anki yön</b>: {aci:.2f}°<br><b>En iyi Yön</b>: {(best_aci):.2f}°</div>',
                    unsafe_allow_html=True
                )
        prev_aci = aci

        #2. İTERASYON
        for loop in range(1):

            #Durdur Butonunun Çalışması :
            if st.session_state.stop:
                logger.info("Navigation stopped by user")
                break

            avg_powers = []
            found_flag = False

            # Arama Fazı, Sağa Dönerek Ölçümler Alıyor
            for i in range(7):     
                
                #Arayüze Açının Bastırılması
                angle_box.markdown(
                    f'<div style="border: 2px solid #4CAF50; padding: 10px; border-radius: 5px; text-align: center;">'
                    f'<b>Şu anki yön</b>: {aci:.2f}°<br><b>En iyi Yön</b>: {(best_aci):.2f}°</div>',
                    unsafe_allow_html=True
                )

                #Sinyallerin hesaplanması:
                latest_power_dbm = get_signal_strength(sdr)
                frequencies, powers = measure_signal_power_wide_rtlsdr(sdr)
                avg_powers = np.append(avg_powers, latest_power_dbm)
                avg_powers = np.array(avg_powers)


                #Arayüze Gücün ve Grafiğin Bastırılması::
                power_box.markdown(
                    f'<div style="border: 2px solid #2196F3; padding: 10px; border-radius: 5px; text-align: center;">'
                    f'<b>Anlık Ölçülen Güç</b>: {latest_power_dbm if latest_power_dbm is not None else "N/A"} dBm</div>',
                    unsafe_allow_html=True
                )
                if powers is not None:
                    fig, ax = plt.subplots()
                    ax.plot(frequencies, powers, label="Signal Power")
                    ax.set_xlabel("Frequency (MHz)")
                    ax.set_ylabel("Power (dBm)")
                    # ax.set_ylim(60, -10)
                    ax.set_title("Spectrum (432–434 MHz)")
                    ax.set_xlim(432e6, 434e6)
                    ax.grid(True)
                    ax.legend()
                    spectrum_plot.pyplot(fig)
                    plt.close(fig)
                if powers is None:
                    logger.error("Failed to measure signal power, skipping")
                    continue

                # Açı ve DBM'in terminale bastırılması.
                logger.info("Turn %d: %.5f dBm, Angle: %.2f°", i, latest_power_dbm, aci)
                
                if i != 6  : #Adım Adım Sola dönülmesi 90,60,30,0,-30,-60,-90:
                    max_index = avg_powers.argmax() # Dizideki GÜçlerin Sıralanması
                    best_aci = prev_aci - (donen_aci*max_index)%360
                    aci = (aci - donen_aci)%360
                    nav.sola_don(gyro, turn_angle, max_duty=rotate_duty_cycle)
                    time.sleep(0.05)

            #Max İndexin Bulunması Sağa Dönme Sayısının Belirlenmesi ve Uygulanması
            max_index = avg_powers.argmax() 
            right_turns_needed = 6 - max_index 
            best_aci = (aci + donen_aci*right_turns_needed)%360
            for j in range(right_turns_needed) :
                aci = (aci + donen_aci)%360
                nav.saga_don(gyro, turn_angle, max_duty=rotate_duty_cycle)
                time.sleep(0.05)

        logger.info("Max signal at index %d, angle %.2f°, turning right %d times, after that moving forward",
        max_index, best_aci, right_turns_needed)        
        nav.ileri(for_dur-1.5, duty_cycle=forward_duty_cycle)
        time.sleep(0.25)



        #3. İTERASYON
        for loop in range(5):

            #Durdur Butonunun Çalışması :
            if st.session_state.stop:
                logger.info("Navigation stopped by user")
                break
            latest_power_dbm1 = get_signal_strength(sdr)

            if stop_treshold < latest_power_dbm1 : 
                    found_flag = True
                    logger.info("kafanı sikim")
                    break

            #Arabanın 90 derece sağa dönmesi
            for k in range (3):
                aci = (aci + donen_aci)%360
                nav.saga_don(gyro, turn_angle, max_duty = rotate_duty_cycle)
                logger.info("ARABA 90 DERECE SAĞA DÖNECEK : Turn %d: Angle: %.2f°", k, aci)
                angle_box.markdown(
                        f'<div style="border: 2px solid #4CAF50; padding: 10px; border-radius: 5px; text-align: center;">'
                        f'<b>Şu anki yön</b>: {aci:.2f}°<br><b>En iyi Yön</b>: {(best_aci):.2f}°</div>',
                        unsafe_allow_html=True
                    )
            prev_aci = aci

            avg_powers = []
            found_flag = False

            # Arama Fazı, Sağa Dönerek Ölçümler Alıyor
            for i in range(7):     

                #Arayüze Açının Bastırılması
                angle_box.markdown(
                    f'<div style="border: 2px solid #4CAF50; padding: 10px; border-radius: 5px; text-align: center;">'
                    f'<b>Şu anki yön</b>: {aci:.2f}°<br><b>En iyi Yön</b>: {(best_aci):.2f}°</div>',
                    unsafe_allow_html=True
                )

                #Sinyallerin hesaplanması:
                latest_power_dbm = get_signal_strength(sdr)
                frequencies, powers = measure_signal_power_wide_rtlsdr(sdr)
                avg_powers = np.append(avg_powers, latest_power_dbm)
                avg_powers = np.array(avg_powers)

                if stop_treshold < latest_power_dbm : 
                    found_flag = True
                    logger.info("kafanı sikim")
                    break


                #Arayüze Gücün ve Grafiğin Bastırılması::
                power_box.markdown(
                    f'<div style="border: 2px solid #2196F3; padding: 10px; border-radius: 5px; text-align: center;">'
                    f'<b>Anlık Ölçülen Güç</b>: {latest_power_dbm if latest_power_dbm is not None else "N/A"} dBm</div>',
                    unsafe_allow_html=True
                )
                if powers is not None:
                    fig, ax = plt.subplots()
                    ax.plot(frequencies, powers, label="Signal Power")
                    ax.set_xlabel("Frequency (MHz)")
                    ax.set_ylabel("Power (dBm)")
                    # ax.set_ylim(60, -10)
                    ax.set_title("Spectrum (432–434 MHz)")
                    ax.set_xlim(432e6, 434e6)
                    ax.grid(True)
                    ax.legend()
                    spectrum_plot.pyplot(fig)
                    plt.close(fig)
                if powers is None:
                    logger.error("Failed to measure signal power, skipping")
                    continue

                # Açı ve DBM'in terminale bastırılması.
                logger.info("Turn %d: %.5f dBm, Angle: %.2f°", i, latest_power_dbm, aci)
                
                if i != 6  : #Adım Adım Sola dönülmesi 90,60,30,0,-30,-60,-90
                    max_index = avg_powers.argmax() # Dizideki GÜçlerin Sıralanması
                    best_aci = prev_aci - (donen_aci*max_index)%360
                    aci = (aci - donen_aci)%360
                    nav.sola_don(gyro, turn_angle, max_duty=rotate_duty_cycle)
                    time.sleep(0.05)
            
            if found_flag:
                logger.info("Navigation stopped due to signal threshold")
                reached_box.markdown(
                    f'<div style="border: 2px solid #FF9800; padding: 10px; border-radius: 5px; text-align: center;">'
                    f'<b>Konuma Ulaşıldı.</b></div>',
                    unsafe_allow_html=True
                )
                break

            #Max İndexin Bulunması Sağa Dönme Sayısının Belirlenmesi ve Uygulanması
            max_index = avg_powers.argmax() 
            right_turns_needed = 6 - max_index 
            best_aci = (aci + donen_aci*right_turns_needed)%360
            for j in range(right_turns_needed) :
                aci = (aci + donen_aci)%360
                nav.saga_don(gyro, turn_angle, max_duty=rotate_duty_cycle)
                time.sleep(0.05)

            logger.info("Max signal at index %d, angle %.2f°, turning right %d times, after that moving forward",
            max_index, best_aci, right_turns_needed) 
             
            nav.ileri(for_dur-1.75, duty_cycle=forward_duty_cycle)

    

    except Exception as e:
        logger.error("Error in vehicle loop: %s", e)
        st.error(f"Hata: {e}")
    finally:
        nav.cleanup()
        gyro.cleanup()  # Added: Cleanup gyroscope
        st.session_state.running = False  # Reset running state
        st.session_state.stop = False  # Reset stop state
        logger.info("Vehicle loop terminated.")
        status_text.write("Navigasyon tamamlandı.")
        sdr.close()
        # st.rerun()  # Force UI refresh

def main():
    # Streamlit UI setup
    st.title("Navigasyon Arayüzü")

    # Create two columns for buttons
    col1, col2 = st.columns(2)

    # Başlat button
    with col1:
        if st.button("Başlat", disabled=st.session_state.running):
            st.session_state.running = True
            st.session_state.stop = False
            st.rerun()  # Force UI refresh

    # Durdur button
    with col2:
        if st.button("Durdur", disabled=not st.session_state.running):
            st.session_state.stop = True
            st.session_state.running = False
            st.rerun()  # Force UI refresh

    # Run navigation if started and not stopped
    if st.session_state.running and not st.session_state.stop:
        run_navigation()

if __name__ == "__main__":
    main()

