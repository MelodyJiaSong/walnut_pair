'use client';

// Main Panel Component

import { Layout } from 'antd';
import { ReactNode } from 'react';
import './mainPanel__style.scss';

const { Content } = Layout;

interface MainPanelProps {
  children: ReactNode;
}

export default function MainPanel({ children }: MainPanelProps) {
  return <Content className="main-panel">{children}</Content>;
}

