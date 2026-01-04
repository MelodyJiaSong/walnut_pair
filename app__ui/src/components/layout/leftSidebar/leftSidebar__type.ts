// Left Sidebar Component Types

import { ReactNode, ComponentType } from 'react';

export interface MenuItem {
  key: string;
  label: string;
  icon?: ComponentType | ReactNode;
  children?: MenuItem[];
  path?: string;
}

export interface LeftSidebarProps {
  collapsed?: boolean;
  onCollapse?: (collapsed: boolean) => void;
}

