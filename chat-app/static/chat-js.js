$(function(){
  $("#nameget").click(function(){
      //alert("start");
  })
});

function test(){
  alert("test in");
}

function send(){
  alert("send in2");
  var fdata = new FormData();
  
  fdata.append("name", "hahaha");
  fdata.append("pass", "testpassword");
  fdata.append("content", "This is content test.");

  $.ajax({
    url: '/1', 
    type: 'POST', 
    data: fdata, 
    contentType: false,
    processData: false,
    success: function(data, datatype){
      console.log('Success', data);
    },
    error: function(XMLHttpRequest, textStatus, errorThrown) {
      //非同期で通信失敗時に読み出される
      console.log('Error : ' + errorThrown);
    }
  });
}
