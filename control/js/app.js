var app = angular.module("streamApp", ['ui.bootstrap', 'ngWebsocket']);

app.factory('slaveService', function($http) {
  return {
    getSlaves: function() {
      //return the promise directly.
      return $http.get('/api/slaves')
        .then(function(result) {
          //resolve the promise as the data
          return result.data;
        });
    },
    getStatus: function() {
      //return the promise directly.
      return $http.get('/api/status')
        .then(function(result) {
          //resolve the promise as the data
          return result.data;
        })
    },
  }
});

app.controller('SlaveListCtrl', function($scope, $timeout, slaveService) {
  $scope.getSlaves = function(){
    slaveService.getSlaves().then(function(slaves) {
      $scope.slaves = slaves;
      $scope.cache_bypass = Date.now();
    });
  };
  // Function to replicate setInterval using $timeout service.
  $scope.intervalFunction = function(){
    $timeout(function() {
      $scope.getSlaves();
      $scope.intervalFunction();
    }, 5000)
  };

  $scope.getSlaves();
  // Kick off the interval
  $scope.intervalFunction();

});

app.controller('StatusCtrl', function($scope, $timeout, slaveService) {
  $scope.getStatus = function(){
    slaveService.getStatus().then(function(status) {
      $scope.status = status;
    });
  };
  // Function to replicate setInterval using $timeout service.
  $scope.intervalFunction = function(){
    $timeout(function() {
      $scope.getStatus();
      $scope.intervalFunction();
    }, 3000)
  };

  $scope.getStatus();
  // Kick off the interval
  $scope.intervalFunction();
});

app.controller('StreamCtrl', function($scope, $http) {
  $scope.url = '';

  $scope.start_stream = function() {
    $http.post('/api/start-stream', { url: $scope.url, slave: $scope.selectedSlave.name }).success(function(data) { });
  };

  $scope.stop_stream = function() {
    $http.post('/api/stop-stream', { slave: $scope.selectedSlave.name }).success(function(data) { });
  };
});

app.controller('ImageAPICtrl', function($scope, $http) {
  $scope.url = '';

  $scope.display_image = function() {
    $http.post('/api/display-image', { url: $scope.url, slave: $scope.selectedSlave.name }).success(function(data) { });
  };

  $scope.hide_image = function() {
    $http.post('/api/hide-image', { slave: $scope.selectedSlave.name }).success(function(data) { });
  };
});

app.controller('CommandModalCtrl', function ($scope, $modal, slaveService) {

  $scope.open = function (selected) {

    var modalInstance = $modal.open({
      animation: true,
      templateUrl: 'command_modal.html',
      controller: 'CommandModalInstanceCtrl',
      resolve: {
        slaves: function () {
          return slaveService.getSlaves();
        },
        selected: function() {
          return selected || null;
        }
      }
    });

    modalInstance.result.then(function (selectedItem) {
      $scope.selected = selectedItem;
    }, function () {
      $log.info('Modal dismissed at: ' + new Date());
    });
  };
});

app.controller('CommandModalInstanceCtrl', function ($scope, $modalInstance, $filter, $log, slaves, selected) {

  var all_slaves = {"name": "*"};
  slaves.unshift(all_slaves);
  $scope.slaves = slaves;

  if (selected)
  {
    var slave = $filter("filter")(slaves, {name: selected}, true);
    $log.info(slave);
    $scope.selectedSlave = slave[0];
  }
  else
  {
    $scope.selectedSlave = all_slaves;
  }

  $scope.ok = function () {
    $modalInstance.close();
  };

  $scope.cancel = function () {
    $modalInstance.dismiss('cancel');
  };
});

app.controller('LogCtrl', function ($scope, $websocket) {
  /*var ws = $websocket.$new({
        url: 'ws://127.0.0.1:8080/log', 
        reconnect: true
  });
  console.log("Opening log dispatcher connection ...");
  $scope.log_messages = "";

  ws.$on('$open', function () {
    console.log("Connection to log dispatcher opened!");
  })
  .$on('log', function (message) { // it listents for 'incoming event'
    $scope.log_messages += "\n" + message
  });*/
});
