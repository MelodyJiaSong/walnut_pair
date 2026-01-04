// Theme Configuration

export type Theme = 'light' | 'dark';

export interface ThemeConfig {
  name: Theme;
  label: string;
}

export const themes: ThemeConfig[] = [
  { name: 'light', label: 'Light' },
  { name: 'dark', label: 'Dark' },
];

export const defaultTheme: Theme = 'light';

