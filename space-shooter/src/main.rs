// TODO(Adriano) YAML reader and configuration for the map (map builder, etc...)
use macroquad::prelude::{
    clear_background, draw_circle, draw_rectangle, is_key_down, next_frame, KeyCode, BLACK, RED,
    WHITE, YELLOW,
};
use std::collections::HashSet;

mod game;
mod vec2;
use game::{CircleParameters, Controller, RectangleParameters, Shape, Sprite, SpriteType, World};
use vec2::Vec2;

// Define this here to make life easier
const G: f32 = 0.1;
const eps: f32 = 0.01; // Don't let it get too low :P
const friction: f32 = 0.00000001;
const max_vel: f32 = 40.0; // isotropic
const bullet_mass: f32 = 0.1; // Usually smaller than the shit below
const bullet_r: f32 = 4.0;
const bullet_addable_tinterval: usize = 60; // _ frames => 1 bullet at most

#[macroquad::main("space-shooter")]
async fn main() {
    // :/
    let max_width = 800.0;

    //////////////// MOVING BOX ////////////////
    // Make sure these are defined outside the loop to avoid going out of scope

    let player_controller1 = Controller {
        up_key_code: KeyCode::Up,
        down_key_code: KeyCode::Down,
        left_key_code: KeyCode::Left,
        right_key_code: KeyCode::Right,
        fire_key_code: KeyCode::Backspace, // TODO(Adriano) how to use spacebar instead?
        key_force: 1.0,
    };

    let player1 = Sprite {
        loc: Vec2 { x: 40.0, y: 40.0 },
        vel: Some(Vec2 { x: 0.0, y: 0.0 }),
        mass: 1.0,
        shape: Shape::Rectangle(RectangleParameters {
            width_x: 40.0,
            width_y: 40.0,
        }),
        sprite_type: SpriteType::Player,
        controller: Some(player_controller1),
        bullet_interval_counter: 0,
    };

    let player_controller2 = Controller {
        up_key_code: KeyCode::W,
        down_key_code: KeyCode::S,
        left_key_code: KeyCode::A,
        right_key_code: KeyCode::D,
        fire_key_code: KeyCode::Tab,
        key_force: 1.0,
    };

    let player2 = Sprite {
        loc: Vec2 {
            x: max_width - 40.0,
            y: max_width - 40.0,
        },
        vel: Some(Vec2 { x: 0.0, y: 0.0 }),
        mass: 1.0,
        shape: Shape::Rectangle(RectangleParameters {
            width_x: 40.0,
            width_y: 40.0,
        }),
        sprite_type: SpriteType::Player,
        controller: Some(player_controller2),
        bullet_interval_counter: 0,
    };

    let sun = Sprite {
        loc: Vec2 {
            x: max_width / 2.0,
            y: max_width / 2.0,
        },
        vel: None, // This does not move
        mass: 10_000.0,
        shape: Shape::Circle(CircleParameters { r: 10.0 }),
        sprite_type: SpriteType::Planet,
        controller: None,           // This is not controllable
        bullet_interval_counter: 0, // stupid shit kms
    };

    let mut game = World {
        sprites: vec![player1, player2, sun],
        dt: 0.1,
    };

    loop {
        // Part 1. Clear
        clear_background(BLACK);

        // Prt 1.5: Remove bullets outside the map
        game.sprites = game
            .sprites
            .iter()
            .filter(|sprite_ref| {
                sprite_ref.sprite_type != SpriteType::Bullet
                    || (sprite_ref.loc.x >= 0.0
                        && sprite_ref.loc.x <= max_width
                        && sprite_ref.loc.y >= 0.0
                        && sprite_ref.loc.y <= max_width)
            })
            .cloned()
            .collect();

        // Part 2. Per-Sprite Updates + Draw
        let sprites_clone = game.sprites.clone(); // Really shit but OK, avoid double-borrow mut
        let mut bullets2add = Vec::<Sprite>::new();
        let mut killedbybullets = HashSet::<usize>::new();
        for (i, sprite1) in (&mut game.sprites).iter_mut().enumerate() {
            let sprite1clone = sprite1.clone(); // shittiest thing ever: do this so that we don't double-reference (sometimes we need to clone for bullet)

            // NOTE that sprite1 should be mutable
            // Part 1: get the sprite information
            let sprite_color = match sprite1.sprite_type {
                SpriteType::Planet => YELLOW,
                SpriteType::Player => WHITE,
                SpriteType::Bullet => RED,
            };

            // Part 2: Update Rules (Force calculations + Bullet Hit/Frame Exit) Logic
            if sprite1.controller.is_some() && sprite1.vel.is_none() {
                panic!("You are not allowed to be controllable, but not kinematic-able");
            }
            match sprite1.vel {
                // TODO(Adriano) just using .vel is kind of janky
                Some(ref mut vel) => {
                    let mut force = Vec2 { x: 0.0, y: 0.0 }; // TODO(Adriano) avoid double-counting this shit!

                    // Part 1: Update based on controller
                    match sprite1.controller {
                        Some(ref controller) => {
                            // Part 1: Force Change based on Controller
                            force.x += if vel.x < max_vel {
                                if is_key_down(controller.left_key_code) {
                                    -controller.key_force
                                } else if is_key_down(controller.right_key_code) {
                                    controller.key_force
                                } else {
                                    0.0
                                }
                            } else {
                                0.0
                            };
                            force.y += if vel.y < max_vel {
                                if is_key_down(controller.up_key_code) {
                                    -controller.key_force
                                } else if is_key_down(controller.down_key_code) {
                                    controller.key_force
                                } else {
                                    0.0
                                }
                            } else {
                                0.0
                            };

                            // Part 2: Spawn Bullets based on controller
                            sprite1.bullet_interval_counter += 1;
                            if is_key_down(controller.fire_key_code)
                                && sprite1.bullet_interval_counter >= bullet_addable_tinterval
                            {
                                // Inherit the momentum: kind of dumb but whatever TODO(Adriano) make a better aiming paradigm
                                let mut bullet = sprite1clone; // kind of shit but ok
                                bullet.loc.x += if bullet.vel.unwrap().x > 0.0 { 50.0 } else { -50.0 }; // Please no hardcody TODO(Adriano)
                                bullet.loc.y += if bullet.vel.unwrap().y > 0.0 { 50.0 } else { -50.0 }; // Please no hardcody TODO(Adriano)
                                bullet.mass = bullet_mass;
                                bullet.shape = Shape::Circle(CircleParameters { r: bullet_r });
                                bullet.sprite_type = SpriteType::Bullet;
                                bullet.controller = None;
                                bullets2add.push(bullet);
                                sprite1.bullet_interval_counter = 0;
                            }
                        }
                        None => {} // NOOP
                    };

                    // Part 2: Update based on n-body simulation
                    for (j, sprite2) in (&sprites_clone).iter().enumerate() {
                        if i != j {
                            // TODO(Adriano) find a cleaner solution to the double-borrow problem with the mutable reference(s)
                            let positionless_scale = sprite1.mass * sprite2.mass * G;
                            let diff = sprite2.loc - sprite1.loc; // sprite2 ON sprite1 (towards sprite2)
                            let norm2 = diff.norm2();
                            let norm32 = norm2 * norm2.sqrt(); // Add sqrt2 to account for normalization of the vector
                            let full_scale = positionless_scale / (norm32 + eps);
                            let force_enacted = diff * full_scale;
                            force.x += force_enacted.x;
                            force.y += force_enacted.y;
                        }
                        // is kill?
                        if i != j
                            && sprite2.sprite_type == SpriteType::Bullet
                            && sprite1.sprite_type == SpriteType::Player
                        {
                            let left = sprite1.loc.x;
                            let right = sprite1.loc.x + 40.0; // TODO(Adriano) no hardcody plz
                            let top = sprite1.loc.y;
                            let bot = sprite1.loc.y + 40.0; // TODO(Adriano) no hardcody plz
                            if left <= sprite2.loc.x
                                && sprite2.loc.x <= right
                                && top <= sprite2.loc.y
                                && sprite2.loc.y <= bot
                            {
                                killedbybullets.insert(i);
                            }
                        }
                    }

                    // Part 3. Add viscosity/friction/drag for better player experience
                    {
                        force.x -= friction * vel.x;
                        force.y -= friction * vel.y;
                    }

                    // Part 4: Clip and set positions and velocities (Kinematics equations)
                    {
                        let acc = Vec2 {
                            x: force.x / sprite1.mass,
                            y: force.y / sprite1.mass,
                        };
                        vel.x += acc.x * game.dt;
                        vel.y += acc.y * game.dt;
                        sprite1.loc.x += vel.x;
                        sprite1.loc.y += vel.y;
                        if sprite1.loc.x <= 0.0 {
                            sprite1.loc.x = 0.0;
                            vel.x = 0.0;
                        } else if sprite1.loc.x >= max_width {
                            sprite1.loc.x = max_width;
                            vel.x = 0.0;
                        } else if sprite1.loc.y <= 0.0 {
                            sprite1.loc.y = 0.0;
                            vel.y = 0.0;
                        } else if sprite1.loc.y >= max_width {
                            sprite1.loc.y = max_width;
                            vel.y = 0.0;
                        }
                    }
                }
                None => {} // NOOP
            };

            // Part 3: Draw the sprite
            match sprite1.shape {
                Shape::Circle(circle_parameters) => {
                    draw_circle(
                        sprite1.loc.x,
                        sprite1.loc.y,
                        circle_parameters.r,
                        sprite_color,
                    );
                }
                Shape::Rectangle(rectangle_parameters) => {
                    draw_rectangle(
                        sprite1.loc.x,
                        sprite1.loc.y,
                        rectangle_parameters.width_x,
                        rectangle_parameters.width_y,
                        sprite_color,
                    );
                }
            };
        }

        // Part 2.5: Add this dummy shit for next iteration (lmao this is stupid)
        game.sprites = game
            .sprites
            .iter()
            .chain(bullets2add.iter())
            .cloned()
            .collect(); // super shit TODO(Adriano)

        // Part 2.99999999: filter those that died
        game.sprites = game
            .sprites
            .iter()
            .enumerate()
            .filter(|(i, _)| !killedbybullets.contains(i))
            .map(|(_, sprite)| sprite.clone())
            .collect();

        // Part 5. Display
        next_frame().await
    }
}
