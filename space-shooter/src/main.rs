use macroquad::prelude::*;

#[macroquad::main("MyGame")]
async fn main() {
    // Make sure these are defined outside the loop to avoid going out of scope
    let mut x = 40.0;
    let mut y = 40.0;
    
    loop {
        clear_background(BLACK);
        
        // Create a sprite
        draw_rectangle(x, y, 120.0, 60.0, WHITE);

        // Handle the keys
        if is_key_down(KeyCode::Up) {
            y -= 1.0;
        } else if is_key_down(KeyCode::Down) {
            y += 1.0;
        }
        if is_key_down(KeyCode::Left) {
            x -= 1.0;
        }
        if is_key_down(KeyCode::Right) {
            x += 1.0;
        }

        next_frame().await
    }
}