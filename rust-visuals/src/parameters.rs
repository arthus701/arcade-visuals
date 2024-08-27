use ndarray::prelude::*;

#[derive(Serialize, Deserialize)]
struct AnimationParameters {
    num_points: u32,
    ang_arg_div: u32,
    angs: Vec<f32>,
    form_span: u16,
    form_1: Vec<u32>,
    form_2: Vec<u32>,
    formfreq_span: u32,
    formfreq_list: Vec<f32>,
    add_span: u32,
    add_list: Vec<f32>,
    mul_span: u32,
    mul_list: Vec<f32>,
    bgcolor_span: u32,
    bgcolor_list: Vec<Vec<u32>>,
    bgtail_span: u32,
    bgtail_list: Vec<u32>,
    bgseed_span: u32,
    bgseed_list: Vec<u32>,
    bgfreq_span: u32,
    bgfreq_list: Vec<f32>,
}

impl Default for AnimationParameters {
    const ANG_RESO: u32 = 1001;

    fn default() -> Self {
        Self {
            num_points: 5000,
            angs: Array::linspace(0.0, 360.0, AnimationParameters::ANG_RESO),
            ang_arg_div: 20,
            form_span: 3,
            form_1: vec![0, 150, 270],
            form_2: vec![0, 90, 180, 270],
            formfreq_span: 200,
            formfreq_list: vec![1.0 / 200.0, 1.0 / 100.0, 1.0 / 500.0, 1.0 / 10.0],
            add_span: 20,
            add_list: vec![1.0, 0.5, 0.1],
            mul_span: 26,
            mul_list: vec![1.0, 0.5, 0.1],
            bgcolor_span: 1200,
            bgcolor_list: vec![
                vec![255, 0, 0],
                vec![200, 0, 155],
                vec![200, 0, 255],
                vec![255, 0, 255],
                vec![100, 0, 100],
            ],
            bgtail_span: 40,
            bgtail_list: vec![10, 255, 100, 200],
            bgseed_span: 30,
            bgseed_list: vec![
                66359, 23802, 72212, 87422, 93711, 60901, 102507, 86383, 85871, 29174, 67382,
                31268, 49904, 46217, 36448, 4085, 83402, 100324, 38140, 45713, 43896, 16853, 86778,
                3440, 76750, 14508, 19974, 87937, 25580, 49236, 14495, 41940, 69652, 15417, 50981,
                73977, 74383, 48582, 54104, 45674, 99805, 3940, 14555, 59095, 44172, 42904, 50004,
                68999, 9507, 87843, 100043, 88797, 74890, 60940, 53515, 51485, 10603, 57034, 89593,
                54704, 50310, 70297, 36594, 41455, 71175, 16918, 18941, 16480, 69407, 98259, 66323,
                60134, 55220, 74973, 40513, 68977, 58235, 51438, 10734, 22637, 19618, 78404, 52584,
                33885, 88093, 43323, 49493, 95712, 96190, 27274, 95760, 15794, 11261, 16946, 12098,
                48366, 100148, 14988, 76259, 53729,
            ],
            bgfreq_span: 200,
            bgfreq_list: vec![1.0 / 200.0, 1.0 / 100.0, 1.0 / 500.0, 1.0 / 10.0],
        }
    }
}
