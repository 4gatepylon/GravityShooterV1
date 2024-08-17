use crate::vec2::Vec2;
use macroquad::prelude::KeyCode;

//////////////// SHAPE INFORMATION ////////////////
// TODO(Adriano) stop copying/cloning shit plz
#[derive(Copy, Clone)]
pub struct CircleParameters {
    pub r: f32,
}

#[derive(Copy, Clone)]
pub struct RectangleParameters {
    pub width_x: f32,
    pub width_y: f32,
}
#[derive(Copy, Clone)]
pub enum Shape {
    Circle(CircleParameters),
    Rectangle(RectangleParameters),
}
////////////////////////////////

//////////////// SPRITES ////////////////
#[derive(Copy, Clone, PartialEq)]
pub enum SpriteType {
    // Planets and players do not respond to kinematic information, but bullets do
    Planet,
    Bullet,
    Player,
}

#[derive(Copy, Clone)]
pub struct Controller {
    pub up_key_code: KeyCode,
    pub down_key_code: KeyCode,
    pub left_key_code: KeyCode,
    pub right_key_code: KeyCode,
    pub fire_key_code: KeyCode,
    pub key_force: f32, // isotropic
}

#[derive(Copy, Clone)]
pub struct Sprite {
    pub loc: Vec2,
    pub vel: Option<Vec2>,
    pub mass: f32,
    pub shape: Shape,
    pub sprite_type: SpriteType,
    pub controller: Option<Controller>,
    pub bullet_interval_counter: usize,
}

#[derive(Clone)] // Only clone
pub struct World {
    pub sprites: Vec<Sprite>,
    pub dt: f32, // timestep size, used for approximate integration
}
////////////////////////////////
