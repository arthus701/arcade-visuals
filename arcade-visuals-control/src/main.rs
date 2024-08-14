use eframe::egui;
use std::net::{IpAddr, SocketAddr, SocketAddrV4, SocketAddrV6};
use std::net::UdpSocket;
use serde::{Deserialize, Serialize};
use egui::FontFamily::Proportional;
use egui::{FontId, Label, Sense};
use egui::TextStyle::*;

fn main() -> eframe::Result {

    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default().with_inner_size([800.0, 800.0]),
        ..Default::default()
    };

    eframe::run_native(
        "Arcade Visuals Controller",
        options,
        Box::new(|cc| {
            Ok(Box::new(VisualsController::new(cc)))
        }),
    )
}

struct VisualsController {
    socket: UdpSocket,
    clients: Vec<SocketAddr>,
    params: Parameters,
}

impl VisualsController {
    fn new(cc: &eframe::CreationContext<'_>) -> Self {
        let ctx = cc.egui_ctx.clone();

        let mut style = (*ctx.style()).clone();

        // Redefine text_styles
        style.text_styles = [
          (Heading, FontId::new(30.0, Proportional)),
          (Name("Heading2".into()), FontId::new(25.0, Proportional)),
          (Name("Context".into()), FontId::new(23.0, Proportional)),
          (Body, FontId::new(18.0, Proportional)),
          (Monospace, FontId::new(14.0, Proportional)),
          (Button, FontId::new(18.0, Proportional)),
          (Small, FontId::new(10.0, Proportional)),
        ].into();
        
        // Mutate global style with above changes
        ctx.set_style(style);

        Self::default()
    }

    fn add_client(&mut self, listen: IpAddr, port: u16) {
        let socket_addr = match listen {
            IpAddr::V4(addr) => SocketAddr::V4(SocketAddrV4::new(addr, port)),
            IpAddr::V6(addr) => SocketAddr::V6(SocketAddrV6::new(addr, port, 0, 0)),
        };

        self.clients.push(socket_addr)
    }
}

impl Default for VisualsController {
    fn default() -> Self {
        Self {
            socket: UdpSocket::bind("0.0.0.0:36780").expect("failed to bind"),
            clients: vec![],
            params: Parameters::default()
        }
    }


}

#[derive(Serialize, Deserialize)]
struct Parameters {
    num_points: u32,
    form_span: u16,
    form_1: Vec<u32>,
    form_2: Vec<u32>,
    formfreq_span: u32,
    formfreq_list: Vec<f32>,
    add_span: u32,
    add_list: Vec<f32>,
    mul_span: u32,
    mul_list: Vec<f32>,
    ang_arg_div: u32,
}

impl Default for Parameters {
    fn default() -> Self {
        Self {
            num_points: 5000,
            form_span: 3,
            form_1: vec![
                0,
                150,
                270
            ],
            form_2: vec![
                0,
                90,
                180,
                270,
            ],
            formfreq_span: 200,
            formfreq_list: vec![
                1.0/200.0, 1.0/100.0, 1.0/500.0, 1.0/10.0
            ],
            add_span: 20,
            add_list: vec![1.0, 0.5, 0.1],
            mul_span: 26,
            mul_list: vec![
                1.0, 0.5, 0.1
            ],
            ang_arg_div: 200
        }
    }
}


impl eframe::App for VisualsController {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        egui::CentralPanel::default().show(ctx, |ui| {
            ui.heading("Arcade Visuals Controller");
            ui.horizontal(|ui| {
                ui.label("N Points Cloud");
                ui.add(egui::Slider::new(&mut self.params.num_points, 0..=8000));

            });
            ui.add(egui::Slider::new(&mut self.params.form_span, 0..=100).text("Form Span"));

            let mut to_remove = None;
            for (pos, e) in &mut self.params.form_1.iter_mut().enumerate() {
                ui.horizontal(|ui| {
                    ui.add(egui::Slider::new(e, 0..=360).text(format!("Form 1: {pos}")));
                    if ui.add(Label::new(egui::RichText::new("⊗").color(egui::Color32::RED)).sense(Sense::click())).clicked() {
                        to_remove = Some(pos);
                    }
                });
            }

            if let Some(pos) = to_remove {
                self.params.form_1.remove(pos);
            }

            if ui.button("+ Form 1").clicked() {
                self.params.form_1.push(0);
            }

            if ui.button("push").clicked() {
                self.socket.send_to(&serde_json::to_vec(&self.params).expect("failed to serialize"), "0.0.0.0:46499").expect("failed to send");
            }
        });
    }
}