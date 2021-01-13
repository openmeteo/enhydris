enhydris = {
  mapViewport: [24, 38, 25, 39],
};
require('../static/js/enhydris');

enhydris.map.leafletMap = {
  fitBounds: jest.fn(),
};
window = {}; // eslint-disable-line no-global-assign

describe('setupViewport', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  function checkForCalledWith(expectedLat1, expectedLon1, expectedLat2, expectedLon2) {
    expect(enhydris.map.leafletMap.fitBounds).toHaveBeenCalledTimes(1);
    const [arg] = enhydris.map.leafletMap.fitBounds.mock.calls[0];
    const [latlon1, latlon2] = arg;
    const [lat1, lon1] = latlon1;
    const [lat2, lon2] = latlon2;
    expect(lat1).toBeCloseTo(expectedLat1);
    expect(lon1).toBeCloseTo(expectedLon1);
    expect(lat2).toBeCloseTo(expectedLat2);
    expect(lon2).toBeCloseTo(expectedLon2);
  }

  test('use whole map in small widths', () => {
    window.innerWidth = 991;
    enhydris.map.setupViewport();
    checkForCalledWith(38, 24, 39, 25);
  });

  test('use whole map in small widths with search result', () => {
    window.innerWidth = 991;
    document.body.innerHTML = '<div class="map map-fullpage with-search-result"></div>';
    enhydris.map.setupViewport();
    checkForCalledWith(38, 24, 39, 25);
  });

  test('use part of map in large widths with search result', () => {
    window.innerWidth = 992;
    document.querySelector = (selector) => {
      if (selector === '.with-search-result') {
        return 'mapDiv';
      }
      if (selector === '.search-content-wrapper') {
        return 'searchContentWrapper';
      }
      if (selector === '.search-result') {
        return { clientWidth: 440 };
      }
      return null;
    };
    window.getComputedStyle = (element) => (
      element === 'searchContentWrapper' ? { marginLeft: 50, paddingLeft: 100 } : null
    );
    enhydris.map.setupViewport();
    /* The screen is 992 px wide, but only the rightmost 992 - 440 - 50 - 100 = 402 px
     * are clear, so the viewport should be set so that the rightmost 402 px show the
     * requested 24-25 degrees. The entire 992px-wide map should therefore
     * be 992/402*(25-24) = 2.468 degrees wide; it should therefore span
     * 22.532-25 degrees.
     */
    checkForCalledWith(38, 22.532, 39, 25);
  });
});

describe('enhydris.stationsLayer.getOwnerName', () => {
  beforeAll(() => {
    axios = { // eslint-disable-line no-global-assign
      get: jest.fn(() => Promise.resolve({ data: { name: 'Assassination Bureau, Ltd' } })),
    };
  });

  beforeEach(() => { enhydris.stationsLayer.ownerNames = {}; });

  afterEach(() => jest.clearAllMocks());

  test('returns already registered owner name', async () => {
    enhydris.stationsLayer.ownerNames = { 18: 'Extortion Bureau, Ltd' };
    const result = await enhydris.stationsLayer.getOwnerName(18);
    expect(result).toEqual('Extortion Bureau, Ltd');
  });

  test('returns requested owner name', async () => {
    const result = await enhydris.stationsLayer.getOwnerName(18);
    expect(result).toEqual('Assassination Bureau, Ltd');
  });
});

describe('enhydris.stationsLayer.addStationsPageToStationsLayer', () => {
  const response = {
    data: {
      results: [
        {
          id: 42,
          owner: 18,
          name: 'Hobbiton',
          geom: 'SRID=4326;POINT (20.984238 39.147111)',
        },
        {
          id: 43,
          owner: 18,
          name: 'Rivendell',
          geom: 'SRID=4326;POINT (21.984238 39.547111)',
        },
      ],
    },
  };
  const bindPopup = jest.fn();
  const addTo = jest.fn();
  const marker = { bindPopup, addTo };

  beforeAll(() => {
    L = { marker: jest.fn(() => marker) }; // eslint-disable-line no-global-assign
    enhydris.stationsLayer.ownerNames[18] = 'Assassination Bureau, Ltd';
    enhydris.stationsLayer.addStationsPageToStationsLayer(response);
  });

  test('has created markers', () => {
    expect(L.marker.mock.calls).toEqual([
      [[39.147111, 20.984238]],
      [[39.547111, 21.984238]],
    ]);
  });

  test('has created popups', () => {
    expect(bindPopup.mock.calls).toEqual([
      [`
        <h2>Hobbiton</h2>
        <p>Owner: Assassination Bureau, Ltd</p>
        <p><a href="/stations/42/">Details...</a></p>
      `],
      [`
        <h2>Rivendell</h2>
        <p>Owner: Assassination Bureau, Ltd</p>
        <p><a href="/stations/43/">Details...</a></p>
      `],
    ]);
  });

  test('has added markers to layer', () => {
    expect(marker.addTo.mock.calls).toEqual([
      [enhydris.stationsLayer],
      [enhydris.stationsLayer],
    ]);
  });
});

describe('enhydris.stationsLayer.fillWithStations', () => {
  const responses = [
    { data: { next: 'https://assassinationbureau.com/?page=irrelevant', results: [] } },
    { data: { next: null, results: [] } },
  ];
  let counter = 0;

  beforeAll(() => {
    axios = { // eslint-disable-line no-global-assign
      get: jest.fn(() => {
        const result = Promise.resolve(responses[counter]);
        counter += 1;
        return result;
      }),
    };
    enhydris.stationsLayer.addStationsPageToStationsLayer = jest.fn();
    enhydris.stationsLayer.fillWithStations();
  });

  test('has made two requests', () => {
    expect(axios.get.mock.calls).toEqual([
      ['/api/stations/'],
      ['https://assassinationbureau.com/?page=irrelevant'],
    ]);
  });
});
