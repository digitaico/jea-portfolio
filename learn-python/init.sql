-- Initialize database for image processor
-- This script runs when the PostgreSQL container starts for the first time
-- Compatible with PostgreSQL 16+

-- Create extension for UUID support (if needed)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create the transformation_history table with modern PostgreSQL features
CREATE TABLE IF NOT EXISTS transformation_history (
    id BIGSERIAL PRIMARY KEY,
    image_path VARCHAR(500) NOT NULL,
    transformation_type VARCHAR(100) NOT NULL,
    parameters JSONB,
    output_path VARCHAR(500),
    processing_time INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance (using modern PostgreSQL features)
CREATE INDEX IF NOT EXISTS idx_transformation_history_type ON transformation_history(transformation_type);
CREATE INDEX IF NOT EXISTS idx_transformation_history_created_at ON transformation_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transformation_history_image_path ON transformation_history(image_path);
CREATE INDEX IF NOT EXISTS idx_transformation_history_parameters ON transformation_history USING GIN (parameters);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
DROP TRIGGER IF EXISTS update_transformation_history_updated_at ON transformation_history;
CREATE TRIGGER update_transformation_history_updated_at
    BEFORE UPDATE ON transformation_history
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert some sample data (optional)
INSERT INTO transformation_history (image_path, transformation_type, parameters, output_path, processing_time)
VALUES 
    ('sample1.jpg', 'brightness', '{"factor": 1.3}', 'output1.jpg', 150),
    ('sample2.jpg', 'sepia', '{}', 'output2.jpg', 200),
    ('sample3.jpg', 'gaussian_blur', '{"kernel_size": 5}', 'output3.jpg', 300)
ON CONFLICT DO NOTHING;

-- Create a view for recent transformations
CREATE OR REPLACE VIEW recent_transformations AS
SELECT 
    id,
    image_path,
    transformation_type,
    parameters,
    output_path,
    processing_time,
    created_at,
    updated_at
FROM transformation_history
WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY created_at DESC;

-- Grant permissions (if needed for external connections)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres; 