import packageJson from '../package.json';

export const environment = {
  name : packageJson.name,
  production: true,
  apiUrl: `${window.location.protocol}//${window.location.hostname}${window.location.port ? `:${window.location.port}` : ''}`,
  apiDateFormat:"YYYY-MM-DDTHH:mm:ss.SSS[Z]",
  version : packageJson.version
};