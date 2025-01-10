#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Installing frontend dependencies...${NC}"

# Install dependencies
npm install \
  @emotion/react@^11.11.3 \
  @emotion/styled@^11.11.0 \
  @mui/material@^5.15.3 \
  @mui/icons-material@^5.15.3 \
  @types/react@^18.2.47 \
  @types/react-dom@^18.2.18 \
  axios@^1.6.5 \
  react@^18.2.0 \
  react-dom@^18.2.0 \
  react-router-dom@^6.21.1 \
  typescript@^4.9.5

echo -e "${GREEN}Frontend dependencies installed successfully!${NC}"

# Create types directory if it doesn't exist
mkdir -p src/types

# Create environment.d.ts if it doesn't exist
if [ ! -f "src/types/environment.d.ts" ]; then
  echo -e "${YELLOW}Creating environment.d.ts...${NC}"
  cat > src/types/environment.d.ts << EOL
declare namespace NodeJS {
  interface ProcessEnv {
    REACT_APP_API_URL: string;
  }
}
EOL
  echo -e "${GREEN}Created environment.d.ts${NC}"
fi

echo -e "${GREEN}Frontend setup completed!${NC}"
