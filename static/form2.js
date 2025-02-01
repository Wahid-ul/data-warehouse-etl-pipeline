$('#prev1').click(function(e){
    e.stopImmediatePropagation() ;
});

$('#next1').click(function(e){
    array2=[]; //empty array 
});
   

$('#next2').click(function(e){
    e.preventDefault();
    var Initial_weight = $("#Initial_weight").val();
    var Texture = $("#Texture").val();
    var Location = $("#Location").val();
    var Collection_date = $("#Collection_date").val();
    var Remarks = $("#Remarks").val();
    var today=new Date();
    var enteredDate = new Date(Collection_date);

    //values=[];
    //values.length=5;
    //adding elements to the array
    
    if (!Initial_weight || !Texture || !Location || !Collection_date) {
        //alert("Please fill out all required fields");
        e.stopImmediatePropagation() ;//prevents every event from running
        //document.getElementById("Initial_weight").placeholder = "***must be filled!";
        document.getElementById("Initial_weight").placeholder = "***must be filled!";
        document.getElementById("Texture").placeholder = "***must be filled!";
        document.getElementById("Location").placeholder = "***must be filled!";
        document.getElementById("Collection_date").placeholder = "***must be filled!";
        document.getElementById("Remarks").placeholder = "***must be filled!";
        return false;
    }
    else if(enteredDate > today){
        e.stopImmediatePropagation();
        document.getElementById("futureDate").innerHTML = "***date cannot be in the future!";
        document.getElementById("numeric1").innerHTML = "***must be a number!";
        return false;

    }
    else if (isNaN(Initial_weight)) {
        e.stopImmediatePropagation() ;//prevents every event from running
        document.getElementById("numeric1").innerHTML = "***must be a number!";
        return false;
    
    }
    else if (!/^[a-zA-Z]+$/.test(Texture) ) {
        e.stopImmediatePropagation() ;//prevents every event from running
        document.getElementById("alphabetic1").innerHTML = "***must contain only letter!";
        
        return false;

    }else if (!/^[a-zA-Z]+$/.test(Location) ) {
        e.stopImmediatePropagation() ;//prevents every event from running
        document.getElementById("alphabetic2").innerHTML = "***must contain only letter!";
        
        return false;}
    else{
        //console.log("datastructure value "+values)
        array2.push(Initial_weight);
        array2.push(Texture);
        array2.push(Location);
        array2.push(Collection_date);
        array2.push(Remarks);
        console.log("array2.length"+array2.length)
        if(array2.length==5){
        $.ajax({
            type:"POST",
            url:"/form2",
            data:{
                //Barcode:$("#Barcode").val(),
                Initial_weight:array2[0],
                Texture:array2[1],
                Location:array2[2],
                Collection_date:array2[3],
                Remarks:array2[4],       
                
                
                
            },
            success:function(result){
                //alert('ok');
                console.log(result);
                document.getElementById("id_a2").innerHTML = result;
                
            },
            error:function(error){
                console.log(error);
            }

        });
    }
    }
  });
  $('#exit2').click(function(e){
    e.preventDefault();
    var Initial_weight = $("#Initial_weight").val();
    var Texture = $("#Texture").val();
    var Location = $("#Location").val();
    var Collection_date = $("#Collection_date").val();
    var Remarks = $("#Remarks").val();
    var today=new Date();
    var enteredDate = new Date(Collection_date);

    //values=[];
    //values.length=5;
    //adding elements to the array
    
    if (!Initial_weight || !Texture || !Location || !Collection_date) {
        //alert("Please fill out all required fields");
        e.stopImmediatePropagation() ;//prevents every event from running
        //document.getElementById("Initial_weight").placeholder = "***must be filled!";
        document.getElementById("Initial_weight").placeholder = "***must be filled!";
        document.getElementById("Texture").placeholder = "***must be filled!";
        document.getElementById("Location").placeholder = "***must be filled!";
        document.getElementById("Collection_date").placeholder = "***must be filled!";
        document.getElementById("Remarks").placeholder = "***must be filled!";
        return false;
    }
    else if(enteredDate > today){
        e.stopImmediatePropagation();
        document.getElementById("futureDate").innerHTML = "***date cannot be in the future!";
        document.getElementById("numeric1").innerHTML = "***must be a number!";
        return false;

    }
    else if (isNaN(Initial_weight)) {
        e.stopImmediatePropagation() ;//prevents every event from running
        document.getElementById("numeric1").innerHTML = "***must be a number!";
        return false;
    
    }
    else if (!/^[a-zA-Z]+$/.test(Texture) ) {
        e.stopImmediatePropagation() ;//prevents every event from running
        document.getElementById("alphabetic1").innerHTML = "***must contain only letter!";
        
        return false;

    }else if (!/^[a-zA-Z]+$/.test(Location) ) {
        e.stopImmediatePropagation() ;//prevents every event from running
        document.getElementById("alphabetic2").innerHTML = "***must contain only letter!";
        
        return false;}
    else{
        //console.log("datastructure value "+values)
        edit_array2.push(Initial_weight);
        edit_array2.push(Texture);
        edit_array2.push(Location);
        edit_array2.push(Collection_date);
        edit_array2.push(Remarks);
        console.log("array2.length"+array2.length)
        if(edit_array2.length==5 ){
        $.ajax({
            type:"POST",
            url:"/form2",
            data:{
                //Barcode:$("#Barcode").val(),
                Initial_weight:edit_array2[0],
                Texture:edit_array2[1],
                Location:edit_array2[2],
                Collection_date:edit_array2[3],
                Remarks:edit_array2[4],       
                
                
                
            },
            success:function(result){
                //alert('ok');
                console.log(result);
                window.location.href="http://192.168.130.245:5000/dashboard";
            
            },
            error:function(error){
                console.log(error);
            }

        });
    }
    }
  });

//To prevent entering duplicate values after going back to a previous page,

