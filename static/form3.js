$('#prev1').click(function(e){
    e.stopImmediatePropagation() ;
});
$('#next1').click(function(e){
    array3=[]; //empty array 
});   



$('#next3').click(function(e){
    e.preventDefault();
    //let G_image = document.getElementById("Gel_image").files[0];
    //var form_data1 = new FormData();
    //form_data1.append("G_image", G_image);
     //var form_data= new FormData($('#Gel_image')[0]);
     //let Gel_image = document.getElementById("Gel_image").files[0];
     //let G_img = new FormData();
     //G_img.append("Gel_image", Gel_image);
     //console.log("reutwidvdgv"+G_img);
     //fetch('/form3', {method: "POST", body: G_img});
    var Kit_name=$("#Kit_name").val();   
    var Lot_no=$("#Lot_no").val();   
    var Quantity=$("#Quantity").val();   
    var Qubit_conc=$("#Qubit_conc").val();             
    var Nanodrop_conc=$("#Nanodrop_conc").val();
    var Nanodrop_260_280=$("#Nanodrop_260_280").val();
    var Nanodrop_260_230=$("#Nanodrop_260_230").val();
    var Extraction_date=$("#Extraction_date").val();
    var Repeat_no=$("#Repeat_no").val();
    var Remarks=$("#Remarks").val();
    var today=new Date();
    var enteredDate = new Date(Extraction_date);
    
    
    
    if (!Qubit_conc || !Nanodrop_conc || !Nanodrop_260_280 || !Nanodrop_260_230 || !Extraction_date || !Repeat_no || !Remarks) {
        //alert("Please fill out all required fields");
        e.stopImmediatePropagation() ;//prevents every event from running
        //document.getElementById("Initial_weight").placeholder = "***must be filled!";
        document.getElementById("Qubit_conc").placeholder = "***must be filled!";
        document.getElementById("Nanodrop_conc").placeholder = "***must be filled!";
        document.getElementById("Nanodrop_260_280").placeholder = "***must be filled!";
        document.getElementById("Nanodrop_260_230").placeholder = "***must be filled!";
        document.getElementById("Extraction_date").placeholder = "***must be filled!";
        document.getElementById("Repeat_no").placeholder = "***must be filled!";
        document.getElementById("Remarks").placeholder = "***must be filled!";
        return false;
    }else if(enteredDate > today ){
        e.stopImmediatePropagation();
        document.getElementById("extrDate").innerHTML = "***date cannot be in the future!";
        return false;
    }
    else if(isNaN(Lot_no)){
        e.stopImmediatePropagation();
        document.getElementById("ltno.").innerHTML = "***must be a number!";
        return false;
    }
    else if(isNaN(Quantity) ){
        e.stopImmediatePropagation();
        document.getElementById("qnt").innerHTML = "***must be a number!";
        return false;
    }else if(isNaN(Qubit_conc) ){
        e.stopImmediatePropagation();
        document.getElementById("qbt").innerHTML = "***must be a number!";
        return false;
    }else if(isNaN(Nanodrop_conc) ){
        e.stopImmediatePropagation();
        document.getElementById("nano").innerHTML = "***must be a number!";
        return false;
    }
    else if(isNaN(Nanodrop_260_280) ){
        e.stopImmediatePropagation();
        document.getElementById("n280").innerHTML="**must be a number!";
        return false;
        }
    else if(isNaN(Nanodrop_260_230) ){
        e.stopImmediatePropagation();
        document.getElementById("n230").innerHTML="***must be a number!";
        return false;
    }
    else if(isNaN(Repeat_no) ){
        e.stopImmediatePropagation();
        document.getElementById("rpno.").innerHTML="***must be a number!";
        return false;
    }
    /*else if(!/^[a-zA-Z]+$/.test(Remarks)){
        e.stopImmediatePropagation();
        document.getElementById("rmarks").innerHTML="***must contain only letter!";
        return false;
    }*/
            
    else {
        array3.push(Kit_name);
        array3.push(Lot_no);
        array3.push(Quantity);
        array3.push(Qubit_conc);
        array3.push(Nanodrop_conc);
        array3.push(Nanodrop_260_280);
        array3.push(Nanodrop_260_230);
        array3.push(Extraction_date);
        array3.push(Repeat_no);
        array3.push(Remarks);
        console.log("array3.length:"+array3.length)
        if(array3.length==10){
        $.ajax({
            
            type:"POST",
            url:"/form3",

            data:{
                //Barcode:$("#Barcode").val(),
                Kit_name:Kit_name,
                Lot_no:Lot_no,
                Quantity:Quantity,
                //G_img,
                //Gel_image:form_data,
                Qubit_conc:Qubit_conc,       
                
                Nanodrop_conc:Nanodrop_conc,
                Nanodrop_260_280:Nanodrop_260_280,
                Nanodrop_260_230:Nanodrop_260_230,
                Extraction_date:Extraction_date,
                Repeat_no:Repeat_no,
                Remarks:Remarks,
                
                
            },
            
            success:function(result){
                //alert('ok');
                console.log(result);
                document.getElementById("id_a3").innerHTML = result;
                
            },
            error:function(error){
                console.log("error1!")
            }

        });
    }
        
    }  
    
  });

  $('#exit3').click(function(e){
    e.preventDefault();
    if(confirm("DO you want to save?")){
    $.ajax({
        type:"POST",
        url:"/form3",
        data:{
            Kit_name:$("#Kit_name").val(),
            Lot_no:$("#Lot_no").val(),
            Quantity:$("#Quantity").val(),   
            Qubit_conc:$("#Qubit_conc").val(),             
            Nanodrop_conc:$("#Nanodrop_conc").val(),
            Nanodrop_260_280:$("#Nanodrop_260_280").val(),
            Nanodrop_260_230:$("#Nanodrop_260_230").val(),
            Extraction_date:$("#Extraction_date").val(),
            Repeat_no:$("#Repeat_no").val(),
            Remarks:$("#Remarks").val(),
            
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
