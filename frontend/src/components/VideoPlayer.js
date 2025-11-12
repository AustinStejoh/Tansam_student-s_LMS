import React, { useEffect, useRef } from 'react';
import Plyr from 'plyr';
import 'plyr/dist/plyr.css';

const VideoPlayer = ({ url, onEnded }) => {
  const videoRef = useRef(null);
  const playerRef = useRef(null);

  useEffect(() => {
    if (videoRef.current && !playerRef.current) {
      playerRef.current = new Plyr(videoRef.current, {
        controls: [
          'play-large',
          'play',
          'progress',
          'current-time',
          'mute',
          'volume',
          'settings',
          'fullscreen'
        ],
        settings: ['quality', 'speed'],
        quality: {
          default: 720,
          options: [4320, 2880, 2160, 1440, 1080, 720, 576, 480, 360, 240]
        },
        speed: {
          selected: 1,
          options: [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2]
        }
      });

      if (onEnded) {
        videoRef.current.addEventListener('ended', onEnded);
      }
    }

    return () => {
      if (playerRef.current) {
        playerRef.current.destroy();
      }
      if (videoRef.current && onEnded) {
        videoRef.current.removeEventListener('ended', onEnded);
      }
    };
  }, [onEnded]);

  return (
    <video
      ref={videoRef}
      className="plyr-react plyr"
      crossOrigin="anonymous"
      playsInline
    >
      <source src={url} type="video/mp4" />
    </video>
  );
};

export default VideoPlayer;