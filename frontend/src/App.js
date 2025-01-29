import React, { useState } from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  Button, 
  Paper, 
  Grid,
  AppBar,
  Toolbar,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';
import VideocamIcon from '@mui/icons-material/Videocam';

function App() {
  const [selectedExercise, setSelectedExercise] = useState('push_up');
  const [isExercising, setIsExercising] = useState(false);

  const exercises = [
    { id: 'push_up', name: 'Push-ups' },
    { id: 'squat', name: 'Squats' },
    { id: 'hammer_curl', name: 'Hammer Curls' }
  ];

  const startExercise = () => {
    setIsExercising(true);
    fetch('http://localhost:5000/start-exercise', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ exercise: selectedExercise }),
    });
  };

  const stopExercise = () => {
    setIsExercising(false);
    fetch('http://localhost:5000/stop-exercise', {
      method: 'POST'
    });
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static" sx={{ backgroundColor: '#1a237e' }}>
        <Toolbar>
          <FitnessCenterIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Fitneed Trainer
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Grid container spacing={3} justifyContent="center">
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 4, height: '100%', textAlign: 'center' }}>
              <Typography variant="h5" gutterBottom sx={{ mb: 4 }}>
                Select Exercise
              </Typography>
              <FormControl fullWidth sx={{ mb: 4 }}>
                <InputLabel>Exercise</InputLabel>
                <Select
                  value={selectedExercise}
                  label="Exercise"
                  onChange={(e) => setSelectedExercise(e.target.value)}
                >
                  {exercises.map((exercise) => (
                    <MenuItem key={exercise.id} value={exercise.id}>
                      {exercise.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Button
                variant="contained"
                size="large"
                sx={{ 
                  mt: 2, 
                  py: 1.5, 
                  px: 4, 
                  fontSize: '1.1rem',
                  minWidth: '200px'
                }}
                onClick={isExercising ? stopExercise : startExercise}
                color={isExercising ? "error" : "primary"}
                startIcon={<VideocamIcon />}
              >
                {isExercising ? "Stop Exercise" : "Start Exercise"}
              </Button>
              
              {isExercising && (
                <Typography variant="body1" sx={{ mt: 4, color: 'text.secondary' }}>
                  Exercise window is now open. Press 'q' to close the exercise window.
                </Typography>
              )}
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

export default App;
