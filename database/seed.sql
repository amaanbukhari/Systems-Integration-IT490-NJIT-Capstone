-- Sample Users
INSERT INTO users (username, email, password_hash) VALUES
('alice', 'alice@example.com', '$2b$12$examplehash1'),
('bob', 'bob@example.com', '$2b$12$examplehash2');

-- Sample Songs
INSERT INTO songs (title, artist, genre, duration, song_url) VALUES
('Shape of You', 'Ed Sheeran', 'Pop', 240, 'http://example.com/songs/shape_of_you.mp3'),
('Blinding Lights', 'The Weeknd', 'R&B', 200, 'http://example.com/songs/blinding_lights.mp3');

-- Sample Playlists
INSERT INTO playlists (user_id, name) VALUES
(1, 'Workout Hits'),
(2, 'Chill Vibes');

-- Sample Playlist Songs
INSERT INTO playlist_songs (playlist_id, song_id) VALUES
(1, 1),
(1, 2),
(2, 2);

-- Sample Likes
INSERT INTO likes (user_id, song_id) VALUES
(1, 1),
(2, 2);

-- Sample Listening History
INSERT INTO listening_history (user_id, song_id) VALUES
(1, 1),
(2, 2),
(1, 2);

-- Sample Chats
INSERT INTO chats (user1_id, user2_id) VALUES
(1, 2);

-- Sample Messages
INSERT INTO messages (chat_id, sender_id, message) VALUES
(1, 1, 'Hey Bob, check out this song!'),
(1, 2, 'Looks good, Alice!');

-- Sample Shared Links
INSERT INTO shared_links (song_id, user_id, share_token) VALUES
(1, 1, 'share123'),
(2, 2, 'share456');

-- Sample Song Metrics
INSERT INTO song_metrics (song_id, play_count, like_count) VALUES
(1, 10, 5),
(2, 8, 3);
