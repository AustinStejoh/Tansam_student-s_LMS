import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Button,
  Box,
  CircularProgress,
  LinearProgress,
  Alert,
} from '@mui/material';
import VideoPlayer from '../components/VideoPlayer';
import { fetchTopic, markTopicCompleted } from '../utils/api';

const TopicDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [topic, setTopic] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const loadTopic = async () => {
      try {
        const response = await fetchTopic(id);
        setTopic(response.data);
      } catch (error) {
        setError('Failed to load topic content. Please try again.');
        console.error('Error loading topic:', error);
      } finally {
        setLoading(false);
      }
    };

    loadTopic();
  }, [id]);

  const handleProgress = (value) => {
    setProgress(value);
  };

  const handleComplete = async () => {
    try {
      await markTopicCompleted(id);
      // Show completion message or navigate to next topic
    } catch (error) {
      console.error('Error marking topic as complete:', error);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  if (!topic) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="info">Topic not found.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          {topic.title}
        </Typography>
        
        {topic.video_file && (
          <Box sx={{ mb: 4 }}>
            <VideoPlayer
              src={topic.video_file}
              onProgress={handleProgress}
              onComplete={handleComplete}
            />
            <LinearProgress
              variant="determinate"
              value={progress}
              sx={{ mt: 2 }}
            />
          </Box>
        )}

        {topic.ppt_file && (
          <Box sx={{ mt: 4 }}>
            <Typography variant="h6" gutterBottom>
              Presentation Materials
            </Typography>
            <Button
              variant="outlined"
              color="primary"
              href={topic.ppt_file}
              target="_blank"
              rel="noopener noreferrer"
            >
              Download Presentation
            </Button>
          </Box>
        )}

        <Box sx={{ mt: 4 }}>
          <Typography variant="body1" paragraph>
            {topic.description}
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default TopicDetail;