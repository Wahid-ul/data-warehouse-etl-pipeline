$('#prev1').click(function(e){
    e.stopImmediatePropagation() ;
});


$('#next1').click(function(e){
    array4=[]; //empty array 
});   


$('#next4').click(function(e){
    e.preventDefault();
    Run_ID=$("#Run_ID").val();
    //Dna_extraction=$("#Dna_extraction").val();
    Extraction_Startdate=$("#Extraction_Startdate").val();
    Extraction_enddate=$("#Extraction_enddate").val();
    var ex_start=new Date();
    var enter_ex_start=new Date(Extraction_Startdate);
    var ex_end=new Date();
    var enter_ex_end=new Date(Extraction_enddate);
    Yield_nanodrop=$("#Yield_nanodrop").val();
    Yield_qubit=$("#Yield_qubit").val();
    //Gel_image:$("#Gel_image").val(),
    Library_startdate=$("#Library_startdate").val();
    Library_enddate=$("#Library_enddate").val();
    var lib_start=new Date();
    var enter_lib_start=new Date(Library_startdate);
    var lib_end=new Date();
    var enter_lib_end=new Date(Library_enddate);
    Flowcell_id=$("#Flowcell_id").val();
    Native_barcode=$("#Native_barcode").val();
    Active_pores=$("#Active_pores").val();
    Pores_remaining=$("#Pores_remaining").val();
    Loading_start=$("#Loading_start").val();
    Loading_end=$("#Loading_end").val();
    var load_start=new Date();
    var enter_load_start=new Date(Loading_start);
    var load_end=new Date();
    var enter_load_end=new Date(Loading_end);
    Sequencing_status=$("#Sequencing_status").val();
    Sequencing_duration=$("#Sequencing_duration").val();
    Status=$("#Status").val();
                    
    if (!Run_ID  || !Extraction_Startdate || !Extraction_enddate || !Yield_nanodrop  || !Yield_qubit) {
        //alert("Please fill out all required fields");
        e.stopImmediatePropagation() ;//prevents every event from running
        //document.getElementById("Initial_weight").placeholder = "***must be filled!";
        document.getElementById("Run_ID").placeholder = "***must be filled!";
        document.getElementById("Extraction_Startdate").placeholder = "***must be filled!";
        document.getElementById("Extraction_enddate").placeholder = "***must be filled!";
        document.getElementById("Yield_nanodrop").placeholder = "***must be filled!";
        document.getElementById("Yield_qubit").placeholder = "***must be filled!";
        
        return false;} 
    else if(enter_ex_start> ex_start ){
        e.stopImmediatePropagation() ;
        document.getElementById("ex_start").innerHTML = "***date cannot be in the future!";
        return false;
    }else if(enter_ex_end> ex_end){
        e.stopImmediatePropagation() ;
        document.getElementById("ex_end").innerHTML = "***date cannot be in the future!";
        return  false;
    }else if(enter_lib_start> lib_start){
        e.stopImmediatePropagation() ;
        document.getElementById("lib_start").innerHTML = "***date cannot be in the future!";
        return false;
    }else if(enter_lib_end> lib_end){
        e.stopImmediatePropagation() ;
        document.getElementById("lib_end").innerHTML = "***date cannot be in the future!";
        return false;
    }else if(enter_load_start > lib_start){
        e.stopImmediatePropagation() ;
        document.getElementById("load_start").innerHTML = "***date cannot be in the future!";
        return false;
    }else if(enter_load_end> load_end){
        e.stopImmediatePropagation() ;
        document.getElementById("load_end").innerHTML = "***date cannot be in the future!";
        return false;
    }else if(enter_ex_start>enter_ex_end){
        e.stopImmediatePropagation() ;
        document.getElementById("ex_start").innerHTML = "***Starting date should be less than ending date!";
        return false;
    }else if(enter_ex_end> enter_lib_start){
        e.stopImmediatePropagation() ;
        document.getElementById("ex_end").innerHTML = "***extraction ending date should be less from library preparation date!";
        return false;
    }else if(enter_lib_start>enter_lib_end){
        e.stopImmediatePropagation() ;
        document.getElementById("lib_start").innerHTML = "***Library preparation date should be less than its finishing date!";
        return false;
    }else if(enter_lib_end>enter_load_start ){
        e.stopImmediatePropagation() ;
        document.getElementById("lib_end").innerHTML = "***library end should be less than loading date!";
        return false;
    }else if (enter_load_start>enter_load_end){
        e.stopImmediatePropagation() ;
        document.getElementById("load_start").innerHTML = "***loading date cant be greater than its ending date!";
        return  false;
    }
    else{
        array4.push(Run_ID);
        array4.push(Extraction_Startdate);
        array4.push(Extraction_enddate);
        array4.push(Yield_nanodrop);
        array4.push(Yield_qubit);
        array4.push(Library_startdate);
        array4.push(Library_enddate);
        array4.push(Flowcell_id);
        array4.push(Native_barcode);
        array4.push(Active_pores);
        array4.push(Pores_remaining);
        array4.push(Loading_start);
        array4.push(Loading_end);
        array4.push(Sequencing_status);
        array4.push(Sequencing_duration);
        array4.push(Status);
        


        console.log("array4.length:"+array4.length)
        if(array4.length==16){
        
            $.ajax({
                type:"POST",
                url:"/form4",
                data:{
                    //Barcode:$("#Barcode").val(),
                    Run_ID:Run_ID,
                    Extraction_Startdate:Extraction_Startdate,
                    Extraction_enddate:Extraction_enddate,
                    Yield_nanodrop:Yield_nanodrop,
                    Yield_qubit:Yield_qubit,       
                    
                    //Gel_image:Gel_image,
                    Library_startdate:Library_startdate,
                    Library_enddate:Library_enddate,
                    Flowcell_id:Flowcell_id,
                    Native_barcode:Native_barcode,
                    Active_pores:Active_pores,
                    Pores_remaining:Pores_remaining,
                    Loading_start:Loading_start,
                    Loading_end:Loading_end,
                    Sequencing_status:Sequencing_status,
                    Sequencing_duration:Sequencing_duration,
                    Status:Status
                    
                    
                },
                success:function(result){
                    //alert('ok');
                    console.log(result);
                    document.getElementById("id_a4").innerHTML = result;
                    
                }

            });
        }
   }
  });

  $('#exit4').click(function(e){
    e.preventDefault();
    if(confirm("DO you want to save?")){
    $.ajax({
        type:"POST",
        url:"/form4",
        data:{
                    Run_ID:Run_ID,
                    Extraction_Startdate:Extraction_Startdate,
                    Extraction_enddate:Extraction_enddate,
                    Yield_nanodrop:Yield_nanodrop,
                    Yield_qubit:Yield_qubit,       
                    
                    //Gel_image:Gel_image,
                    Library_startdate:Library_startdate,
                    Library_enddate:Library_enddate,
                    Flowcell_id:Flowcell_id,
                    Native_barcode:Native_barcode,
                    Active_pores:Active_pores,
                    Pores_remaining:Pores_remaining,
                    Loading_start:Loading_start,
                    Loading_end:Loading_end,
                    Sequencing_status:Sequencing_status,
                    Sequencing_duration:Sequencing_duration,
                    Status:Status
            
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
