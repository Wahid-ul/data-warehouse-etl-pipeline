$('#next1').click(function(e){
    e.preventDefault();
    var Barcode = document.getElementById("Barcode").value;
        var Confirm_Barcode = document.getElementById("Confirm_Barcode").value;
        if (!Barcode) {
            //confirm("Invalid barcode. Please enter an alphanumeric barcode ");
            e.preventDefault();
            //window.location.href="http://127.0.0.1:5000/index";
            document.getElementById("Barcode").placeholder = "***must be filled!";
            document.getElementById("Confirm_Barcode").placeholder = "***must be filled!";
            e.stopImmediatePropagation() ;//prevents every event from running
            
            return false;
          }
        else if(Barcode!=Confirm_Barcode){
            //confirm("Barcode does not match");
            e.preventDefault();
            //window.location.href="http://127.0.0.1:5000/index";
            
            document.getElementById("Barcode_Confirm_Barcode").innerHTML = "***Barcode & Confirm barcode should be same";
            //document.getElementById("Confirm_Barcode").placeholder = "***barcode & confirm barcode should be same";
            e.stopImmediatePropagation() ; //prevents every event from running
            return false;
        }
        else
        {
        $.ajax({
            type:"POST",
            url:"/form1",
            data:{
                Barcode    
            },
            
            success:function(result){
                if(result=="Barcode already exists"){
                    
                    window.location.href="http://127.0.0.1:5000/index";
                    alert(result);
                    //document.getElementById("Barcode_Confirm_Barcode").innerHTML = "Barcode already exists";
                    e.stopImmediatePropagation() ; //prevents every event from running
                    return false
                }                                
                else{
                    alert(result);
                    console.log(result);
                
                    document.getElementById("id_a1").innerHTML = result;
                    
                }
            },
            error:function(error){
                console.log(error);
            }
            
        });
    }        
});
/*
$(function () {
    $("#next1").click(function (e) {
        var Barcode = document.getElementById("Barcode").value;
        var Confirm_Barcode = document.getElementById("Confirm_Barcode").value;
        if(Barcode!=Confirm_Barcode){
            confirm("Barcode does not match");
            e.preventDefault();
            return false;
        }
        
    });
});*/
$('#exit1').click(function(exits){
    exits.preventDefault();
    
    if(confirm("DO you want to save?")){
    $.ajax({
        type:"POST",
        url:"/form1",
        data:{
            Barcode:$("#Barcode").val(),
            
            
          
            
            
        },
        success:function(result){
            //alert("Do you want to save and exit?");
            console.log(result);
            window.location.href="http://192.168.130.245:5000/dashboard";
            
        },
        error:function(error){
            console.log(error);
        }

    });
}
                
});

