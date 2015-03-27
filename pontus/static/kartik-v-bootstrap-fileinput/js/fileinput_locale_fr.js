/*!
 * FileInput <language> Translations - Template file for copying and creating other translations
 *
 * This file must be loaded after 'fileinput.js'. Patterns in braces '{}', or
 * any HTML markup tags in the messages must not be converted or translated.
 *
 * @see http://github.com/kartik-v/bootstrap-fileinput
 *
 * NOTE: this file must be saved in UTF-8 encoding.
 */
(function ($) {
    "use strict";

    $.fn.fileinput.locales.fr = {
        fileSingle: 'fichier',
        filePlural: 'fichiers',
        browseLabel: 'Parcourir &hellip;',
        removeLabel: 'Supprimer',
        removeTitle: 'Supprimer les fichiers selectionnés',
        cancelLabel: 'Annuler',
        cancelTitle: 'Abandonner le téléchargement en cours',
        uploadLabel: 'Télécharger',
        uploadTitle: 'Télécharger les fichiers selectionnés',
        msgSizeTooLarge: 'Fichier "{name}" (<b>{size} KB</b>) dépasse la taille maximale autorisée de téléchargement de <b>{maxSize} KB</b>. Se il vous plaît réessayer votre téléchargement!',
        msgFilesTooLess: 'Vous devez sélectionner au moins <b>{n}</b> {files} à télécharger. Se il vous plaît réessayer votre téléchargement!',
        msgFilesTooMany: 'Number of files selected for upload <b>({n})</b> exceeds maximum allowed limit of <b>{m}</b>. Please retry your upload!',
        msgFileNotFound: 'Fichier "{name}" non trouvé!',
        msgFileSecured: 'Security restrictions prevent reading the file "{name}".',
        msgFileNotReadable: 'Fichier "{name}" n\'est pas lisible.',
        msgFilePreviewAborted: 'Aperçu du fichier interrompu pour "{name}".',
        msgFilePreviewError: 'Une erreur est survenue lors de la lecture du fichier "{name}".',
        msgInvalidFileType: 'Type non valide pour le fichier "{name}". Seuls les types de fichiers "{types}" sont pris en charge.',
        msgInvalidFileExtension: 'Extension non valide pour le fichier "{name}". Seuls les extensions "{extensions}" sont pris en charge.',
        msgValidationError: 'File Upload Error',
        msgLoading: 'Loading file {index} of {files} &hellip;',
        msgProgress: 'Loading file {index} of {files} - {name} - {percent}% completed.',
        msgSelected: '{n} files selected',
        msgFoldersNotAllowed: 'Drag & drop files only! Skipped {n} dropped folder(s).',
        dropZoneTitle: 'Drag & drop files here &hellip;'
    };

    $.extend($.fn.fileinput.defaults, $.fn.fileinput.locales.fr);
})(window.jQuery);
