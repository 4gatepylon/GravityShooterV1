use std::ops::{Mul, Sub};

//////////////// Linear Algebra ////////////////

#[derive(Copy, Clone)]
pub struct Vec2 {
    // TODO(Adriano)
    // 1. Generic
    // 2. More dimensions (more generic)
    // 3. More efficient (stop copying and cloning everything)
    pub x: f32,
    pub y: f32,
}

impl Sub for Vec2 {
    type Output = Self;

    fn sub(self, other: Self) -> Self {
        Self {
            x: self.x - other.x,
            y: self.y - other.y,
        }
    }
}

// Same but for broadcast
// By Claude3.5
impl Mul<f32> for Vec2 {
    type Output = Vec2;

    fn mul(self, rhs: f32) -> Self::Output {
        Vec2 {
            x: self.x * rhs,
            y: self.y * rhs,
        }
    }
}

impl Mul<Vec2> for f32 {
    type Output = Vec2;

    fn mul(self, rhs: Vec2) -> Self::Output {
        Vec2 {
            x: self * rhs.x,
            y: self * rhs.y,
        }
    }
}

////////////////////////////////

impl Vec2 {
    pub fn norm2(&self) -> f32 {
        self.x * self.x + self.y * self.y
    }
    // NOTE: unused :/
    // fn dot(&self, other: &Vec2) -> f32 {
    //     self.x * other.x + self.y + other.y
    // }
    // fn cos(&self, other: &Vec2) -> f32 {
    //     let d = self.dot(other);
    //     let n1 = self.norm2().sqrt();
    //     let n2 = other.norm2().sqrt();
    //     return d / (n1 * n2);
    // }
}
