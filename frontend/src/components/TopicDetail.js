import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  LinearProgress,
  Dialog,
  IconButton,
  Button,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import DownloadIcon from '@mui/icons-material/Download';
import AssignmentIcon from '@mui/icons-material/Assignment';
import QuizIcon from '@mui/icons-material/Quiz';
import { useApp } from '../contexts/AppContext';
import VideoPlayer from './VideoPlayer';

const TopicDetail = ({ topic }) => {
  const [videoOpen, setVideoOpen] = useState(false);
  const navigate = useNavigate();
  const { user } = useApp();

  const handleVideoClose = () => {
    setVideoOpen(false);
  };

  return (
    <>
      <Card elevation={0} sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Typography variant="h5" component="h1" sx={{ flex: 1 }}>
              {topic.title}
            </Typography>
          </Box>

          {topic.video_url && (
            <Box sx={{ mb: 3 }}>
              <Button
                variant="contained"
                color="primary"
                startIcon={<PlayArrowIcon />}
                onClick={() => setVideoOpen(true)}
                sx={{ mr: 2 }}
              >
                Watch Video
              </Button>
              {topic.ppt_file && (
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  href={topic.ppt_file}
                  target="_blank"
                >
                  Download Presentation
                </Button>
              )}
            </Box>
          )}

          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <QuizIcon sx={{ mr: 1 }} />
                    <Typography variant="h6">Practice Quiz</Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Test your knowledge with multiple choice questions.
                  </Typography>
                  <Button variant="contained" color="secondary" onClick={() => navigate(`/mcq/${topic.id}`)}>
                    Start MCQ Test
                  </Button>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <AssignmentIcon sx={{ mr: 1 }} />
                    <Typography variant="h6">Assignments</Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    View and submit your assignments for this topic.
                  </Typography>
                  <Button 
                    variant="contained" 
                    color="secondary"
                    onClick={() => navigate(`/assignments/${topic.id}`)}
                  >
                    View Assignments
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Dialog
        fullScreen
        open={videoOpen}
        onClose={handleVideoClose}
        sx={{
          '& .MuiDialog-paper': {
            background: '#000',
          },
        }}
      >
        <Box sx={{ p: 2, display: 'flex', justifyContent: 'flex-end' }}>
          <IconButton
            edge="start"
            color="inherit"
            onClick={handleVideoClose}
            aria-label="close"
            sx={{ color: '#fff' }}
          >
            <CloseIcon />
          </IconButton>
        </Box>
        <Box sx={{ height: 'calc(100% - 64px)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <VideoPlayer 
            url={topic.video_url} 
            onEnded={() => {
              // Mark topic as completed when video ends
              fetch(`/api/topics/${topic.id}/mark_completed/`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
              });
            }}
          />
        </Box>
      </Dialog>
    </>
  );
};

export default TopicDetail;