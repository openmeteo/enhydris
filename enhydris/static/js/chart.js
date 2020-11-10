$(function() {
	// Global configuration values
	const config = {
		blue: "#008FFB",
		gray: "#546E7A",
	};

	/* When attempting to select section of the mini ("small") chart,
	the `selection` event of the chart is executed multiple times for each
	mouse drags. Since the `refetchChart` function is part of the `selection`
	event, this causes multiple API calls to the chart endpoint before the user
	has completed the selection. This is not efficient. Thus, by using the
	`debounce` function, we can create another function that delay the execution
	of the `refetchChart` function by a certain amount of milliseconds, in order
	to give the user enough time to complete the selection. 
	*/
	const debounceRefetchChart = debounce(refetchChart, 200);

	// Main ("big") chart
	const mainChartOption = {
		series: [{
			data: []
		}],
		noData: {
			text: enhydris.strLoading
		},
		chart: {
			id: "mainChart",
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
					refetchChart(xaxis);
					miniChart.updateOptions({
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

	const mainChart = new ApexCharts(
		document.querySelector("#chart-main"),
		mainChartOption
	);
	mainChart.render();

	// Mini ("small") chart
	const miniChartOptions = {
		series: [{
				data: []
		}],
		chart: {
			id: "miniChart",
			height: 100,
			type: "area",
			brush: {
				target: "mainChart",
				enabled: true
			},
			selection: {
				enabled: true
			},
			events: {
				selection: function (chartContext, { xaxis, yaxis }) {
					debounceRefetchChart(xaxis);
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

	const miniChart = new ApexCharts(
		document.querySelector("#chart-mini"),
		miniChartOptions
	);
	miniChart.render();

	// Make API call
	fetch(enhydris.chartApiUrl)
		.then(function (response) {
			return response.json();
		})
		.then(function (data) {
			if (data && data[0]) {
				const mappedData = mapData(data);

				mainChart.updateSeries([
					{
						data: mappedData,
					},
				]);
				miniChart.updateSeries([
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

	function debounce(func, wait, immediate=false) {
		/* Returns a modified callable that waits a certain amount of time
		(i.e. the value of `wait` parameter) before running the function. If the
		function attempts to execute within the wait time, the call is blocked.
		
		To read more about it:
		https://educative.io/edpresso/how-to-use-the-debounce-function-in-javascript
		*/
		let timeout;

		return (...args) => {
			const later = () => {
				timeout = null;
				if (!immediate) func.apply(this, args)
			}
			const callNow = immediate && !timeout;
			clearTimeout(timeout);
			timeout = setTimeout(later, wait);
			if (callNow) func.apply(this, args);
		}
	}
	
	function refetchChart({ min, max }) {
		/* Make API call to fetch & populate chart data between two selected
		data points (i.e. start datetime and end datetime).
		*/
		const startDate = formatDate(min);
		const endDate = formatDate(max);

		mainChart.updateSeries([
			{
				data: [],
			},
		]);
		fetch(`${enhydris.chartApiUrl}?start_date=${startDate}&end_date=${endDate}`)
			.then(response => response.json())
			.then(data => {
				if (data && data[0]) {
					mainChart.updateSeries([
						{
							data: mapData(data)
						},
					]);
				}
			});
	}

	function renderError () {
		document.querySelector("#data_holder").innerHTML =
			`<p>${enhydris.strNoData}</p>`;
	};
});