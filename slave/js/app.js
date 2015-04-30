var app = angular.module("streamApp", []);

app.factory('slaveService', function($http) {
   return {
        getSlaves: function() {
             //return the promise directly.
             return $http.get('/json/slaves')
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
