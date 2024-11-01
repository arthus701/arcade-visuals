

use cpal::Data;
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use rms::Rms;
use spectrum_analyzer::{samples_fft_to_spectrum, FrequencyLimit, FrequencySpectrum};
use spectrum_analyzer::scaling::divide_by_N_sqrt;
use spectrum_analyzer::windows::hann_window;

fn peak_eq_values(freqs: FrequencySpectrum) {
    let mut lowFreqs = vec![];
    let mut midFreqs = vec![];
    let mut highFreqs = vec![];
    for freq in freqs.data() {
        if freq.0 <= 200.0.into() {
            lowFreqs.push(*freq);
        } else if freq.0 <= 2000.0.into()  {
            midFreqs.push(*freq);
        } else if freq.0 <= 20000.0.into() {
            highFreqs.push(*freq);
        }
    }

    let lowFreqsSpec = FrequencySpectrum::new(
        lowFreqs.clone(), 
        freqs.frequency_resolution(), 
        lowFreqs.len().try_into().unwrap(),
        &mut lowFreqs.to_vec()
    );

    // let midFreqsSpec = FrequencySpectrum::new(
    //     midFreqs, 
    //     freqs.frequency_resolution(), 
    //     midFreqs.len(),
    //     midFreqs
    // );

    // let highFreqsSpec = FrequencySpectrum::new(
    //     highFreqs, 
    //     freqs.frequency_resolution(), 
    //     highFreqs.len(),
    //     highFreqs
    // );
}

fn main() {

    println!("Hello, world!");
    let host = cpal::default_host();

    let device = host.default_input_device().expect("no input device available");
    
    let mut supported_configs_range = device.supported_input_configs()
    .expect("error while querying configs");
    
    let supported_config = supported_configs_range.next()
    .expect("no supported config?!")
    .with_max_sample_rate();

    let mut samples = vec![];
    let mut rem_sample = vec![];
    const WINDOW_SIZE_MS: f64 = 10.0;
    let mut rms = Rms::new(WINDOW_SIZE_MS);
    let stream = device.build_input_stream(
        &supported_config.clone().into(),
        move |data: & [f32], _: &cpal::InputCallbackInfo| {

            rms.update(data, in_settings);
            println!("{:?}", rms.avg_at_last_frame());
            samples.extend(data);
            let chunked_samples = samples.chunks(8192);
            for sample in chunked_samples {
                if sample.len() == 8192 {

                let hann_window = hann_window(sample);
                let low_freqs_spec = samples_fft_to_spectrum(
                    &hann_window,
                    44100,
                    FrequencyLimit::Range(20.0, 20000.0),
                    // Recommended scaling/normalization by `rustfft`.
                    Some(&divide_by_N_sqrt),
                ).unwrap();

                let peak = low_freqs_spec.max();

                if peak.1 >= 0.4.into() {
                    println!("{:?}", peak);
                }
                    
                } else {
                    rem_sample = sample.to_vec();
                }                 
            }

            samples = rem_sample.clone();
            
            
            
        },
        move |err| {
            // react to errors here.
        },
        None // None=blocking, Some(Duration)=timeout
    ).unwrap();

    loop {
        stream.play();
    }
}