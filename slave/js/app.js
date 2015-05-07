var app = angular.module("streamApp", []);

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
                        });
        }
   }
});

app.controller('SlaveListCtrl', function($scope, $timeout, slaveService) {
    $scope.getSlaves = function(){
        slaveService.getSlaves().then(function(slaves) {
            $scope.slaves = slaves;
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
        $http.post('/api/start-stream', { url: $scope.url }).success(function(data) { alert(data.message); });
    };

    $scope.stop_stream = function() {
        $http.post('/api/stop-stream', { }).success(function(data) { alert(data.message); });
    };
});
