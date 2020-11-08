$(function() {
	// Global configuration values
	const config = {
		blue: "#008FFB",
		gray: "#546E7A",
	};

	// Debounce function
	const debounceRefetch = debounce(refetch, 200);

	// Line chart
	const optionsLine = {
		series: [{
				data: []
		}],
		noData: {
			text: "Loading..."
		},
		chart: {
			id: "chartLine",
			type: "line",
			height: 230,
			zoom: {
				type: "x",
				enabled: true,
				autoScaleYaxis: true,
			},
			toolbar: {
				autoSelected: "zoom",
				show: true,
				tools: {
					download: true,
					zoomin: true,
					zoomout: true,
					pan: false,
					reset: false
				},
			},
			events: {
				zoomed: function (chartContext, { xaxis }) {
					refetch(xaxis);
					chartArea.updateOptions({
						chart: {
							selection: {
								xaxis: xaxis
							}       
						}
					});
				},
			},
		},
		colors: [config.gray],
		stroke: {
			width: 2
		},
		dataLabels: {
			enabled: false
		},
		fill: {
			opacity: 1
		},
		markers: {
			size: 0
		},
		xaxis: {
			type: "datetime",
			tooltip: {
				enabled: false
			}
		},
		tooltip: {
			enabled: true,
			x: {
				show: true,
				format: "MMM dd, yyyy"
			}
		}
	};

	const chartLine = new ApexCharts(
		document.querySelector("#chart-line"),
		optionsLine
	);
	chartLine.render();

	// Area ("mini") chart
	const optionsArea = {
		series: [{
				data: []
		}],
		chart: {
			id: "chartArea",
			height: 100,
			type: "area",
			brush: {
				target: "chartLine",
				enabled: true
			},
			selection: {
				enabled: true
			},
			events: {
				selection: function (chartContext, { xaxis, yaxis }) {
					debounceRefetch(xaxis);
				}
			},
		},
		colors: [config.blue],
		fill: {
			type: "gradient",
			gradient: {
				opacityFrom: 0.91,
				opacityTo: 0.1
			},
		},
		xaxis: {
			type: "datetime",
			tooltip: {
				enabled: false
			},
			labels: {
				show: true,
				datetimeFormatter: {
					year: "yyyy",
					month: "MMM 'yy",
					day: "dd MMM",
					hour: "HH:mm"
				},
			},
		},
		yaxis: {
			tickAmount: 2
		},
	};

	const chartArea = new ApexCharts(
		document.querySelector("#chart-area"),
		optionsArea
	);
	chartArea.render();

	// Make API call
	fetch(chartApiUrl)
		.then(function (response) {
			return response.json();
		})
		.then(function (data) {
			if (data && data[0]) {
				const mappedData = mapData(data);

				chartArea.updateSeries([
					{
						data: mappedData,
					},
				]);
				chartLine.updateSeries([
					{
						data: mappedData,
					},
				]);
			} else {
				renderError();
			}
		})
		.catch(function () {
			renderError();
		});

	function mapData(data) {
		return data.map((i) => [i.timestamp * 1000, Number(i.value) || 0]);
	}

	function formatDate(timestamp) {
		return new Date(timestamp).toISOString().substring(0, 16);
	}
	
	function debounce(func, wait, immediate) {
		let timeout;

		return function() {
			const context = this;
			const args = arguments;
			const later = function () {
				timeout = null;
				if (!immediate) func.apply(context, args);
			};
			const callNow = immediate && !timeout;
			clearTimeout(timeout);
			timeout = setTimeout(later, wait);
			if (callNow) func.apply(context, args);
		};
	}
	
	function refetch({ min, max }) {
		const startDate = formatDate(min);
		const endDate = formatDate(max);

		chartLine.updateSeries([
			{
				data: [],
			},
		]);
		fetch(`${chartApiUrl}?start_date=${startDate}&end_date=${endDate}`)
			.then(response => response.json())
			.then(data => {
				if (data && data[0]) {
					chartLine.updateSeries([
						{
							data: mapData(data)
						},
					]);
				}
			});
	}

	function renderError () {
		document.querySelector("#data_holder").innerHTML =
			"<h3>No data locally available!</h3>";
	};
});