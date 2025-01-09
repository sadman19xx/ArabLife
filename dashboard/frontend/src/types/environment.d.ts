declare global {
  namespace NodeJS {
    interface ProcessEnv {
      REACT_APP_API_URL: string;
      REACT_APP_DISCORD_CLIENT_ID: string;
      REACT_APP_DISCORD_REDIRECT_URI: string;
      NODE_ENV: 'development' | 'production';
    }
  }
}

export {};
