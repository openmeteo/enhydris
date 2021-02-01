ApexCharts = jest.fn(); // eslint-disable-line
ApexCharts.mockReturnValue({
  render: jest.fn(),
  updateSeries: jest.fn(),
  updateOptions: jest.fn(),
});
const mockFetchSuccess = () => {
  global.fetch = jest.fn(() => Promise.resolve({
    json: () => Promise.resolve([{ timestamp: 1424940, value: 1 }]),
  }));
};
const mockFetchFailure = () => {
  global.fetch = jest.fn(() => Promise.reject(new Error('API is down')));
};

enhydris = {};
require('../static/js/enhydris');

describe('initializeMainChart', () => {
  beforeAll(() => {
    enhydris.chart.initializeMainChart();
  });

  test('creates main chart', () => {
    expect(ApexCharts).toHaveBeenCalled();
  });

  test('renders main chart', () => {
    expect(enhydris.chart.mainChart.render).toHaveBeenCalledWith();
  });
});

describe('initializeMiniChart', () => {
  beforeAll(() => {
    enhydris.chart.initializeMiniChart();
  });

  test('creates mini chart', () => {
    expect(ApexCharts).toHaveBeenCalled();
  });

  test('renderes mini chart', () => {
    expect(enhydris.chart.miniChart.render).toHaveBeenCalledWith();
  });
});

describe('fetchInitialChartData with successful API call', () => {
  beforeAll(() => {
    mockFetchSuccess();
    enhydris.chart.fetchInitialChartData();
  });

  test('update main chart', () => {
    expect(enhydris.chart.mainChart.updateSeries).toHaveBeenCalled();
  });

  test('update mini chart', () => {
    expect(enhydris.chart.miniChart.updateSeries).toHaveBeenCalled();
  });
});

describe('fetchInitialChartData with failed API call', () => {
  beforeAll(() => {
    enhydris.chart.renderError = jest.fn();
    mockFetchFailure();
    enhydris.chart.fetchInitialChartData();
  });

  test('render error', () => {
    expect(enhydris.chart.renderError).toHaveBeenCalled();
  });
});

describe('refetchChart', () => {
  beforeAll(() => {
    mockFetchSuccess();
    const min = 1424940;
    const max = 1425238;
    enhydris.chart.refetchChart({ min, max });
  });

  test('update main chart', () => {
    expect(enhydris.chart.mainChart.updateSeries).toHaveBeenCalled();
  });
});

describe('chartSeries', () => {
  test('chart series with value', () => {
    const data = [{
      timestamp: 1424940, max: 20, min: 10, mean: 15,
    }];
    const result = enhydris.chart.chartSeries(data);
    expect(result).toEqual([
      { data: [[1424940000, 15]], name: 'mean' },
      { data: [[1424940000, 20]], name: 'max' },
      { data: [[1424940000, 10]], name: 'min' },
    ]);
  });

  test('chart series without value', () => {
    const data = [{
      timestamp: 1424940, max: null, min: null, mean: null,
    }];
    const result = enhydris.chart.chartSeries(data);
    expect(result).toEqual([
      { data: [[1424940000, null]], name: 'mean' },
      { data: [[1424940000, null]], name: 'max' },
      { data: [[1424940000, null]], name: 'min' },
    ]);
  });
});
