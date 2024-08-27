
struct RandomInterpolator<T> {
    span: u32,
    statelist: Vec<T>,
    exp: u32,
    seed: Option<Vec<u32>>

}
