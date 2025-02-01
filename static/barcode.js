
$('#button').click(function(e){
  e.preventDefault();
  
  $.ajax({
      type:"POST",
      url:"/zip_upload",
      data:{
          Barcode:$("#Barcode").val()
          
          
        
          
          
      },
      success:function(result){
          //alert(result);
          console.log(result);
          window.location.href = "http://192.168.130.245:5000/upload";
          //window.location.href = "http://127.0.0.1:5000/upload";
          
          
      }

  })
})
