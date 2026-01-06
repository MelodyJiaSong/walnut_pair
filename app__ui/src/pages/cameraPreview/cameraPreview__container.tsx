'use client';

// Camera Preview Container

import { useEffect } from 'react';
import { Row, Col, Button, message, Spin } from 'antd';
import { ReloadOutlined, CameraOutlined, PlayCircleOutlined, StopOutlined } from '@ant-design/icons';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import {
  fetchAvailableCameras,
  startPreview,
  stopPreview,
  captureAll,
} from '../../store/cameraPreview/cameraPreview__saga';
import {
  selectAvailableCameras,
  selectActivePreviews,
  selectLoading,
  selectCapturing,
  selectError,
} from '../../store/cameraPreview/cameraPreview__selector';
import CameraPreviewItem from '../../features/cameraPreview/components/cameraPreviewItem/cameraPreviewItem__component';
import './cameraPreview__style.scss';

export default function CameraPreviewContainer() {
  const dispatch = useAppDispatch();
  const availableCameras = useAppSelector(selectAvailableCameras);
  const activePreviews = useAppSelector(selectActivePreviews);
  const loading = useAppSelector(selectLoading);
  const capturing = useAppSelector(selectCapturing);
  const error = useAppSelector(selectError);

  useEffect(() => {
    dispatch(fetchAvailableCameras());
  }, [dispatch]);

  useEffect(() => {
    if (error) {
      // Show success message if it contains "Successfully captured"
      if (error.includes('Successfully captured')) {
        message.success(error);
      } else {
        message.error(error);
      }
    }
  }, [error]);

  const handleStartPreview = (cameraUniqueId: string) => {
    dispatch(
      startPreview({
        camera_unique_id: cameraUniqueId,
        width: 640,
        height: 480,
      })
    );
  };

  const handleStopPreview = (cameraUniqueId: string) => {
    dispatch(
      stopPreview({
        camera_unique_id: cameraUniqueId,
      })
    );
  };

  const handleRefresh = () => {
    dispatch(fetchAvailableCameras());
  };

  const handleCaptureAll = () => {
    dispatch(captureAll());
  };

  const handlePreviewAll = () => {
    // Dispatch start preview for all cameras that aren't already active
    availableCameras.forEach((cameraInfo) => {
      if (!activePreviews.includes(cameraInfo.unique_id)) {
        dispatch(
          startPreview({
            camera_unique_id: cameraInfo.unique_id,
            width: 640,
            height: 480,
          })
        );
      }
    });
  };

  const handleStopAll = () => {
    // Dispatch stop preview for all active cameras
    activePreviews.forEach((cameraUniqueId) => {
      dispatch(
        stopPreview({
          camera_unique_id: cameraUniqueId,
        })
      );
    });
  };

  if (loading && availableCameras.length === 0) {
    return (
      <div className="camera-preview-loading">
        <Spin size="large" />
        <p style={{ marginTop: 16 }}>Loading cameras...</p>
      </div>
    );
  }

  if (availableCameras.length === 0) {
    return (
      <div className="camera-preview-empty">
        <p>No cameras found</p>
        <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
          Refresh
        </Button>
      </div>
    );
  }

  return (
    <div className="camera-preview-container">
      <div className="camera-preview-header">
        <h2>Camera Preview</h2>
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={handlePreviewAll}
            loading={loading && !capturing}
            disabled={availableCameras.length === 0 || (availableCameras.length === activePreviews.length && activePreviews.length > 0)}
          >
            Preview All
          </Button>
          <Button
            icon={<StopOutlined />}
            onClick={handleStopAll}
            disabled={activePreviews.length === 0}
          >
            Stop All
          </Button>
          <Button
            type="primary"
            icon={<CameraOutlined />}
            onClick={handleCaptureAll}
            loading={capturing}
            disabled={availableCameras.length === 0}
          >
            Capture All
          </Button>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh} loading={loading}>
            Refresh Cameras
          </Button>
        </div>
      </div>

      <Row gutter={[16, 16]}>
        {availableCameras.map((cameraInfo) => {
          // Use unique_id as key to ensure stable mapping
          // Each unique_id uniquely identifies a specific camera device
          return (
            <Col key={cameraInfo.unique_id} xs={24} sm={12} md={8} lg={6}>
              <CameraPreviewItem
                cameraInfo={cameraInfo}
                isActive={activePreviews.includes(cameraInfo.unique_id)}
                onStart={handleStartPreview}
                onStop={handleStopPreview}
              />
            </Col>
          );
        })}
      </Row>
    </div>
  );
}

