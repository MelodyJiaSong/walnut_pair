// Axios API Client Configuration

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';

// Create axios instance with base configuration
const createApiClient = (): AxiosInstance => {
  const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  const apiClient = axios.create({
    baseURL,
    timeout: 150000,  // 150 seconds (2.5 minutes) to accommodate 120 second camera opening timeout + buffer
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor
  apiClient.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      // Add auth token or other headers if needed
      // const token = getAuthToken();
      // if (token) {
      //   config.headers.Authorization = `Bearer ${token}`;
      // }
      return config;
    },
    (error: AxiosError) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor
  apiClient.interceptors.response.use(
    (response: AxiosResponse) => {
      return response;
    },
    (error: AxiosError) => {
      // Handle common errors
      if (error.response) {
        // Server responded with error status
        const status = error.response.status;
        switch (status) {
          case 401:
            // Unauthorized - handle logout
            break;
          case 403:
            // Forbidden
            break;
          case 404:
            // Not found
            break;
          case 500:
            // Server error
            break;
          default:
            break;
        }
      } else if (error.request) {
        // Request made but no response received
        console.error('No response received:', error.request);
      } else {
        // Error setting up request
        console.error('Error:', error.message);
      }
      return Promise.reject(error);
    }
  );

  return apiClient;
};

export const apiClient = createApiClient();

