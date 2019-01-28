const utils = {
  getApiRoot: () => process.env.API_ROOT,
  getAppMode: () => process.env.NODE_ENV,
  getAppTitle: () => process.env.APP_TITLE
};

export default utils;
