import packageJson from '../package.json';

export const environment = {
    name : packageJson.name,
    production: false,
    apiUrl: "http://localhost:5000",
    apiDateFormat:"YYYY-MM-DDTHH:mm:ss.SSS[Z]",
    version : packageJson.version + "-dev"
  };