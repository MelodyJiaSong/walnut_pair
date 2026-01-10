// Menu Configuration

import { DatabaseOutlined } from '@ant-design/icons';
import { MenuItem } from './leftSidebar__type';
import { ReactElement } from 'react';

export const menuItems: MenuItem[] = [
  {
    key: 'walnut-management',
    label: 'Walnut Management',
    icon: DatabaseOutlined as unknown as ReactElement,
    children: [
      {
        key: 'walnut-comparison',
        label: 'Comparison Results',
        path: '/walnut-comparison',
      },
      // Future menu items:
      // {
      //   key: 'walnut-list',
      //   label: 'Walnut List',
      //   path: '/walnut-list',
      // },
      // {
      //   key: 'image-upload',
      //   label: 'Image Upload',
      //   path: '/image-upload',
      // },
    ],
  },
  // Future menu items:
  // {
  //   key: 'settings',
  //   label: 'Settings',
  //   icon: SettingOutlined as unknown as ReactElement,
  //   children: [
  //     {
  //       key: 'user-preferences',
  //       label: 'User Preferences',
  //       path: '/settings/preferences',
  //     },
  //   ],
  // },
];

