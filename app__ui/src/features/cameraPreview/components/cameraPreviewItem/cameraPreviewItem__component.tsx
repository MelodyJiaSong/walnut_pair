'use client';

// Individual Camera Preview Component

import { useEffect, useRef, useState } from 'react';
import { Card, Button, Spin, message } from 'antd';
import { PlayCircleOutlined, StopOutlined } from '@ant-design/icons';
import { CameraInfo, getCameraPreviewWebSocketUrl } from '../../../../api/cameraPreview__api';
import './cameraPreviewItem__style.scss';

interface CameraPreviewItemProps {
  cameraInfo: CameraInfo;
  isActive: boolean;
  onStart: (cameraUniqueId: string) => void;
  onStop: (cameraUniqueId: string) => void;
}

export default function CameraPreviewItem({
  cameraInfo,
  isActive,
  onStart,
  onStop,
}: CameraPreviewItemProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [connecting, setConnecting] = useState(false);

  useEffect(() => {
    // Use cameraInfo.unique_id in dependency array to ensure WebSocket reconnects
    // if the camera changes (though it shouldn't with unique IDs)
    if (isActive) {
      connectWebSocket();
    } else {
      disconnectWebSocket();
    }

    return () => {
      disconnectWebSocket();
    };
  }, [isActive, cameraInfo.unique_id]); // Include unique_id to ensure stable connection

  const connectWebSocket = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    setConnecting(true);
    const wsUrl = getCameraPreviewWebSocketUrl(cameraInfo.unique_id);
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setConnecting(false);
      const displayName = cameraInfo.name || `Camera ${cameraInfo.index}`;
      message.success(`${displayName} connected`);
    };

    ws.onmessage = (event) => {
      // WebSocket sends binary data (JPEG bytes)
      if (event.data instanceof Blob) {
        const reader = new FileReader();
        reader.onload = () => {
          const img = new Image();
          img.onload = () => {
            const canvas = canvasRef.current;
            if (canvas) {
              const ctx = canvas.getContext('2d');
              if (ctx) {
                // Maintain aspect ratio
                const maxWidth = 800;
                const maxHeight = 600;
                let { width, height } = img;
                
                if (width > maxWidth) {
                  height = (height * maxWidth) / width;
                  width = maxWidth;
                }
                if (height > maxHeight) {
                  width = (width * maxHeight) / height;
                  height = maxHeight;
                }
                
                canvas.width = width;
                canvas.height = height;
                ctx.drawImage(img, 0, 0, width, height);
              }
            }
          };
          img.onerror = () => {
            console.error('Failed to load image');
          };
          img.src = reader.result as string;
        };
        reader.onerror = () => {
          console.error('Failed to read blob');
        };
        reader.readAsDataURL(event.data);
      } else if (event.data instanceof ArrayBuffer) {
        // Handle ArrayBuffer
        const blob = new Blob([event.data], { type: 'image/jpeg' });
        const reader = new FileReader();
        reader.onload = () => {
          const img = new Image();
          img.onload = () => {
            const canvas = canvasRef.current;
            if (canvas) {
              const ctx = canvas.getContext('2d');
              if (ctx) {
                const maxWidth = 800;
                const maxHeight = 600;
                let { width, height } = img;
                
                if (width > maxWidth) {
                  height = (height * maxWidth) / width;
                  width = maxWidth;
                }
                if (height > maxHeight) {
                  width = (width * maxHeight) / height;
                  height = maxHeight;
                }
                
                canvas.width = width;
                canvas.height = height;
                ctx.drawImage(img, 0, 0, width, height);
              }
            }
          };
          img.src = reader.result as string;
        };
        reader.readAsDataURL(blob);
      }
    };

    ws.onerror = (error) => {
      setConnecting(false);
      const displayName = cameraInfo.name || `Camera ${cameraInfo.index}`;
      message.error(`${displayName} connection error`);
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      setConnecting(false);
    };

    wsRef.current = ws;
  };

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  const handleToggle = async () => {
    if (isActive) {
      onStop(cameraInfo.unique_id);
    } else {
      // Start preview - this will trigger the Redux saga
      onStart(cameraInfo.unique_id);
      // Note: WebSocket connection will be established automatically when isActive becomes true
    }
  };

  const displayName = cameraInfo.name || `Camera ${cameraInfo.index}`;
  
  return (
    <Card
      title={displayName}
      extra={
        <Button
          type={isActive ? 'default' : 'primary'}
          icon={isActive ? <StopOutlined /> : <PlayCircleOutlined />}
          onClick={handleToggle}
          loading={connecting}
        >
          {isActive ? 'Stop' : 'Start'}
        </Button>
      }
      className="camera-preview-item"
    >
      <div className="camera-preview-content">
        {isActive ? (
          <>
            {connecting && (
              <div className="camera-preview-spinner">
                <Spin size="large" tip="Connecting..." />
              </div>
            )}
            <canvas
              ref={canvasRef}
              className="camera-preview-canvas"
              style={{ display: connecting ? 'none' : 'block' }}
            />
          </>
        ) : (
          <div className="camera-preview-placeholder">
            <p>Click Start to begin preview</p>
          </div>
        )}
      </div>
    </Card>
  );
}

