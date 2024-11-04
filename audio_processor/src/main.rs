use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use serde::{Deserialize, Serialize};
use spectrum_analyzer::scaling::divide_by_N_sqrt;
use spectrum_analyzer::windows::hann_window;
use spectrum_analyzer::{samples_fft_to_spectrum, Frequency, FrequencyLimit, FrequencyValue};
use std::net::UdpSocket;
use std::sync::mpsc::{self, Receiver, Sender};
use std::thread;

const SAMPLING_RATE: u32 = 44100;
const FULL_SPEC_FREQS_RANGE: FrequencyLimit = FrequencyLimit::Range(20.0, 20000.0);
const LOW_SPEC_FREQS_RANGE: FrequencyLimit = FrequencyLimit::Range(20.0, 200.0);
const MID_SPEC_FREQS_RANGE: FrequencyLimit = FrequencyLimit::Range(200.0, 2000.0);
const HIGH_SPEC_FREQS_RANGE: FrequencyLimit = FrequencyLimit::Range(2000.0, 20000.0);

fn main() {
    let (tx_audio_samples, rx_audio_samples) = mpsc::channel();

    let (tx_analyzed_data, rx_analyzed_data) = mpsc::channel();

    spawn_transmit_audio_samples_thread(tx_audio_samples);

    spawn_analyze_audio_samples_thread(rx_audio_samples, tx_analyzed_data);

    let socket = UdpSocket::bind("0.0.0.0:36780").expect("failed to bind");
    loop {
        let analyzed_data = rx_analyzed_data.recv().unwrap();

        println!("{:?}", analyzed_data.rms.limited_value);

        socket
            .send_to(
                &serde_json::to_vec(&analyzed_data)
                    .expect("failed to serialize analyzed audio data"),
                "0.0.0.0:46498",
            )
            .expect("failed to send");
    }
}

fn spawn_transmit_audio_samples_thread(tx_audio_samples: Sender<Vec<f32>>) {
    let host = cpal::default_host();

    let device = host
        .default_input_device()
        .expect("no input device available");

    let mut supported_configs_range = device
        .supported_input_configs()
        .expect("error while querying configs");

    let supported_config = supported_configs_range
        .next()
        .expect("no supported config?!")
        .with_max_sample_rate();

    thread::spawn(move || {
        const CHUNK_SIZE: usize = 4096;
        let mut samples: Vec<f32> = vec![];
        let mut rem_samples: Vec<f32> = vec![];
        let mut tmp_sample: Vec<f32> = vec![];
        let stream = device
            .build_input_stream(
                &supported_config.clone().into(),
                move |data: &[f32], _: &cpal::InputCallbackInfo| {
                    samples.extend(data);
                    let chunked_samples = samples.chunks(CHUNK_SIZE);
                    for sample in chunked_samples {
                        tmp_sample = sample.to_vec().clone();
                        if tmp_sample.len() % CHUNK_SIZE != 0 {
                            rem_samples = tmp_sample.clone();
                            break;
                        }

                        tx_audio_samples.send(tmp_sample.clone()).unwrap();
                    }

                    samples = rem_samples.clone();
                },
                move |err| {
                    println!("{0}", err);
                },
                None,
            )
            .unwrap();

        loop {
            stream.play().expect("couldn't read input");
        }
    });
}

fn spawn_analyze_audio_samples_thread(
    rx_audio_samples: Receiver<Vec<f32>>,
    tx_analyzed_data: Sender<AnalyzedAudioData>,
) {
    thread::spawn(move || {
        let mut last_analyzed_data = AnalyzedAudioData::default();
        loop {
            let samples = rx_audio_samples.recv().unwrap();

            let hann_window = hann_window(&samples);

            let full_freq_spec = samples_fft_to_spectrum(
                &hann_window,
                SAMPLING_RATE,
                FULL_SPEC_FREQS_RANGE,
                Some(&divide_by_N_sqrt),
            )
            .expect("Failed to samples fft to spectrum");

            let mut analyzed_data = AnalyzedAudioData {
                rms: RmsValues::calculate(
                    full_freq_spec.data(),
                    FULL_SPEC_FREQS_RANGE,
                    &last_analyzed_data.rms,
                ),
                low_rms: RmsValues::calculate(
                    full_freq_spec.data(),
                    LOW_SPEC_FREQS_RANGE,
                    &last_analyzed_data.low_rms,
                ),
                mid_rms: RmsValues::calculate(
                    full_freq_spec.data(),
                    MID_SPEC_FREQS_RANGE,
                    &last_analyzed_data.mid_rms,
                ),
                high_rms: RmsValues::calculate(
                    full_freq_spec.data(),
                    HIGH_SPEC_FREQS_RANGE,
                    &last_analyzed_data.high_rms,
                ),
                kick: 0,
            };

            if analyzed_data.low_rms.limited_value > 0.0
            && analyzed_data.rms.limited_value > 0.0 
            {
                analyzed_data.kick = 1;
            }

            tx_analyzed_data.send(analyzed_data).unwrap();

            last_analyzed_data = analyzed_data;
        }
    });
}

#[derive(Serialize, Deserialize, Clone, Copy)]
struct RmsValues {
    value: f32,
    limited_value: f32,
    limit_threshold: f32,
}

impl Default for RmsValues {
    fn default() -> Self {
        Self {
            value: 0.0,
            limited_value: 0.0,
            limit_threshold: 0.0,
        }
    }
}

impl RmsValues {
    fn calculate(
        frequency_spec_data: &[(Frequency, FrequencyValue)],
        frequency_limit: FrequencyLimit,
        last_rms_values: &RmsValues,
    ) -> Self {
        let mut squared_values = vec![];
        for value in frequency_spec_data {
            let freq = value.0.val();

            if freq > frequency_limit.min() && freq < frequency_limit.max() {
                squared_values.push(value.1.val().powf(2.0));
            }
        }

        let squared_sum: f32 = squared_values.iter().sum();

        let squared_avg = squared_sum / squared_values.len() as f32;

        let rms_value = squared_avg.sqrt();

        let mut rms_limited_value = 0.0;
        let mut rms_limit_threshold = last_rms_values.limit_threshold;
        if rms_value > last_rms_values.limit_threshold {
            rms_limited_value = rms_value;
            rms_limit_threshold = rms_value * 0.75;
        } else {
            rms_limit_threshold = rms_limit_threshold * 0.99999999999999;
        }

        RmsValues {
            value: rms_value,
            limited_value: rms_limited_value,
            limit_threshold: rms_limit_threshold,
        }
    }
}

#[derive(Serialize, Deserialize, Clone, Copy)]
struct AnalyzedAudioData {
    rms: RmsValues,
    low_rms: RmsValues,
    mid_rms: RmsValues,
    high_rms: RmsValues,
    kick: i8,
}

impl Default for AnalyzedAudioData {
    fn default() -> Self {
        Self {
            rms: RmsValues::default(),
            low_rms: RmsValues::default(),
            mid_rms: RmsValues::default(),
            high_rms: RmsValues::default(),
            kick: 0,
        }
    }
}