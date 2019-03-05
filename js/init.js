var provider = new firebase.auth.GoogleAuthProvider();

$(document).ready(function() {
   $('.ui.dropdown').dropdown();
   $('.menu .item').tab();
   //$('.ui.sidebar').sidebar('toggle');

   $('#login').click(function(){
       handleLogin();
   })
   firebase.auth().setPersistence(firebase.auth.Auth.Persistence.LOCAL).then(function() {
    }).catch(function(error) {
        // Handle Errors here.
        var errorCode = error.code;
        var errorMessage = error.message;
        showError(error.message);
    });
    firebase.auth().onAuthStateChanged(function(user) {
       if (user) {
           $('#login').text("Log Out");
           $('#name').text('Hi, ' + user.displayName);
       } else {
           $('#login').text("Log In");
           $('#name').text('');
       }
   });
});

function handleLogin(){
    if (firebase.auth().currentUser){
        firebase.auth().signOut()
        .then(function() {
            // Sign-out successful.
            $('#login').text("Log In");
            $('#name').text('');

            window.sessionStorage.removeItem('token')
            window.sessionStorage.removeItem('dict')
            window.sessionStorage.removeItem('updated_cart')
            for (k in calendar_classes){
                removeClassFromCalendar(calendar_classes[k]);
            }
            saved_classes = {}
            calendar_classes = {}
            updateCourseList();
            proc_keyword_data('Unauthorized');
        })
        .catch(function(error) {
            showError(error.message);
        });
    } else {
        firebase.auth().signInWithPopup(provider).then(function(result) {
          // This gives you a Google Access Token. You can use it to access the Google API.
          let token = result.credential.accessToken;
          // The signed-in user info.
          var user = result.user;
          $('#login').text("Log Out");
          $('#name').text('Hi, ' + user.displayName);
          $('.ui.modal.google').modal('hide');

          // ...
        }).catch(function(error) {
          // Handle Errors here.
          var errorCode = error.code;
          var errorMessage = error.message;
          // The email of the user's account used.
          var email = error.email;
          // The firebase.auth.AuthCredential type that was used.
          var credential = error.credential;
          showError(error.message);
          // ...
        });
    }
}

function showError(message){
    error = $.parseHTML(`<div class="ui transition hidden error message">
        <div class="header">
            Something went wrong...
        </div>
        ${message}
    </div>`);
    $('body').append(error)
    $(error).transition({
        animation: 'vertical flip in'
    }).transition({
        animation: 'vertical flip out',
        interval: 5000,
        onComplete: function(){
            $(error).remove();
        }
    })
}
