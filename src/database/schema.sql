CREATE TABLE recipes (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    url TEXT,
    prep_time VARCHAR(50),
    cook_time VARCHAR(50),
    total_time VARCHAR(50),
    servings VARCHAR(10),
    cuisine_type VARCHAR(50),
    difficulty_level VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id)
);

-- User management
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User preferences
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    cuisine_preference TEXT[],
    dietary_restrictions TEXT[],
    excluded_ingredients TEXT[],
    skill_level VARCHAR(20)
);

-- Recipe ratings and reviews
CREATE TABLE recipe_ratings (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER REFERENCES recipes(id),
    user_id INTEGER REFERENCES users(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(recipe_id, user_id)
);

-- Ingredient categories for better matching
CREATE TABLE ingredient_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    parent_category_id INTEGER REFERENCES ingredient_categories(id)
);

-- Enhanced ingredients table
CREATE TABLE ingredients (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER REFERENCES recipes(id),
    category_id INTEGER REFERENCES ingredient_categories(id),
    section VARCHAR(50),
    quantity VARCHAR(50),
    unit VARCHAR(50),
    name VARCHAR(255),
    additional TEXT,
    normalized_name VARCHAR(255), -- For better matching
    UNIQUE(recipe_id, normalized_name)
);

-- User pantry/available ingredients
CREATE TABLE user_ingredients (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    ingredient_name VARCHAR(255),
    quantity VARCHAR(50),
    unit VARCHAR(50),
    expiry_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Save favorite recipes
CREATE TABLE user_favorite_recipes (
    user_id INTEGER REFERENCES users(id),
    recipe_id INTEGER REFERENCES recipes(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, recipe_id)
);

-- Recipe tags for better categorization and search
CREATE TABLE recipe_tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE
);

CREATE TABLE recipe_tag_mappings (
    recipe_id INTEGER REFERENCES recipes(id),
    tag_id INTEGER REFERENCES recipe_tags(id),
    PRIMARY KEY (recipe_id, tag_id)
);

-- Create indexes for frequently accessed columns
CREATE INDEX idx_recipe_title ON recipes(title);
CREATE INDEX idx_ingredient_name ON ingredients(normalized_name);
CREATE INDEX idx_user_email ON users(email);